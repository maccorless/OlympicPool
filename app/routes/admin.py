"""
Admin routes: dashboard, contest management, country import, medal entry, user management.
"""
import csv
import logging
import sqlite3
from datetime import datetime, timezone
from io import StringIO
from flask import render_template, request, redirect, url_for, flash
from app.db import get_db
from app.decorators import admin_required, get_current_user

logger = logging.getLogger(__name__)


def register_routes(app):
    """Register admin routes with Flask app."""

    @app.route('/admin')
    @admin_required
    def admin_dashboard():
        """Admin dashboard - overview of contest status."""
        db = get_db()
        user = get_current_user()

        # Get contest info
        contest = db.execute('SELECT * FROM contest WHERE id = 1').fetchone()

        # Get stats
        total_users = db.execute('SELECT COUNT(*) as count FROM users').fetchone()['count']
        users_with_picks = db.execute('SELECT COUNT(DISTINCT user_id) as count FROM picks').fetchone()['count']
        total_countries = db.execute('SELECT COUNT(*) as count FROM countries WHERE is_active = 1').fetchone()['count']
        total_medals_entered = db.execute('SELECT COUNT(*) as count FROM medals WHERE gold > 0 OR silver > 0 OR bronze > 0').fetchone()['count']

        return render_template('admin/index.html',
                             user=user,
                             contest=contest,
                             total_users=total_users,
                             users_with_picks=users_with_picks,
                             total_countries=total_countries,
                             total_medals_entered=total_medals_entered)

    @app.route('/admin/contest', methods=['GET', 'POST'])
    @admin_required
    def admin_contest():
        """Admin contest configuration."""
        db = get_db()
        user = get_current_user()

        if request.method == 'POST':
            name = request.form.get('name', '').strip()
            state = request.form.get('state', '').strip()
            budget = request.form.get('budget', '').strip()
            max_countries = request.form.get('max_countries', '').strip()
            deadline = request.form.get('deadline', '').strip()

            # Validation
            if not name or not state or not budget or not max_countries or not deadline:
                flash('All fields are required.', 'error')
                return redirect(url_for('admin_contest'))

            try:
                budget = int(budget)
                max_countries = int(max_countries)
            except ValueError:
                flash('Budget and max countries must be integers.', 'error')
                return redirect(url_for('admin_contest'))

            # Validate minimum values
            if budget <= 0 or max_countries <= 0:
                flash('Budget and max countries must be positive integers.', 'error')
                return redirect(url_for('admin_contest'))

            if state not in ('setup', 'open', 'locked', 'complete'):
                flash('Invalid contest state.', 'error')
                return redirect(url_for('admin_contest'))

            # Validate and normalize deadline format
            # Browser datetime-local sends: YYYY-MM-DDTHH:MM
            # We need to store as: YYYY-MM-DDTHH:MM:SSZ
            try:
                # Try parsing as ISO8601 first
                if 'Z' in deadline or '+' in deadline:
                    datetime.fromisoformat(deadline.replace('Z', '+00:00'))
                else:
                    # Browser format - add seconds and Z
                    datetime.fromisoformat(deadline)
                    if len(deadline) == 16:  # YYYY-MM-DDTHH:MM
                        deadline = deadline + ':00Z'
                    elif not deadline.endswith('Z'):
                        deadline = deadline + 'Z'
            except ValueError:
                flash('Invalid deadline format. Use YYYY-MM-DDTHH:MM format.', 'error')
                return redirect(url_for('admin_contest'))

            # Update contest
            try:
                db.execute('''
                    UPDATE contest
                    SET name = ?, state = ?, budget = ?, max_countries = ?, deadline = ?, updated_at = ?
                    WHERE id = 1
                ''', [name, state, budget, max_countries, deadline, datetime.now(timezone.utc).isoformat()])
                db.commit()
                logger.info(f"Contest updated by {user['email']}: state={state}, budget={budget}")
                flash('Contest configuration updated successfully!', 'success')
            except sqlite3.Error as e:
                db.rollback()
                logger.error(f"Failed to update contest: {e}")
                flash('Failed to update contest configuration.', 'error')

            return redirect(url_for('admin_contest'))

        # GET request
        contest = db.execute('SELECT * FROM contest WHERE id = 1').fetchone()
        return render_template('admin/contest.html', user=user, contest=contest)

    @app.route('/admin/countries')
    @admin_required
    def admin_countries():
        """Admin country management."""
        db = get_db()
        user = get_current_user()

        # Show countries list
        countries = db.execute('''
            SELECT * FROM countries ORDER BY cost DESC, name ASC
        ''').fetchall()

        return render_template('admin/countries.html', user=user, countries=countries)

    @app.route('/admin/countries/import', methods=['POST'])
    @admin_required
    def admin_countries_import():
        """Import countries from CSV."""
        db = get_db()
        user = get_current_user()

        csv_data = request.form.get('csv_data', '').strip()

        if not csv_data:
            flash('CSV data is required.', 'error')
            return redirect(url_for('admin_countries'))

        # Parse CSV using csv module (handles quoted fields properly)
        try:
            csv_reader = csv.reader(StringIO(csv_data))
            header = next(csv_reader)

            # Check header
            expected_header = ['code', 'iso_code', 'name', 'expected_points', 'cost']
            if [h.strip().lower() for h in header] != expected_header:
                flash('CSV header must be: code,iso_code,name,expected_points,cost', 'error')
                return redirect(url_for('admin_countries'))

            # Parse data rows
            countries_to_import = []
            for i, row in enumerate(csv_reader, start=2):
                # Skip empty rows
                if not row or all(not field.strip() for field in row):
                    continue

                if len(row) != 5:
                    flash(f'Line {i}: Expected 5 fields, got {len(row)}.', 'error')
                    return redirect(url_for('admin_countries'))

                code, iso_code, name, expected_points_str, cost_str = [field.strip() for field in row]

                # Validate required fields
                if not code or not iso_code or not name:
                    flash(f'Line {i}: code, iso_code, and name are required.', 'error')
                    return redirect(url_for('admin_countries'))

                # Validate numeric fields
                try:
                    expected_points = int(expected_points_str)
                    cost = int(cost_str)
                except ValueError:
                    flash(f'Line {i}: expected_points and cost must be integers.', 'error')
                    return redirect(url_for('admin_countries'))

                countries_to_import.append((code, iso_code, name, expected_points, cost))

        except StopIteration:
            flash('CSV must have header row and at least one data row.', 'error')
            return redirect(url_for('admin_countries'))
        except csv.Error as e:
            flash(f'CSV parsing error: {e}', 'error')
            return redirect(url_for('admin_countries'))

        if not countries_to_import:
            flash('No valid country data found in CSV.', 'error')
            return redirect(url_for('admin_countries'))

        # Import countries (replace all)
        try:
            db.execute('BEGIN')

            # Deactivate all existing countries
            db.execute('UPDATE countries SET is_active = 0')

            # Insert or update countries
            for code, iso_code, name, expected_points, cost in countries_to_import:
                db.execute('''
                    INSERT INTO countries (code, iso_code, name, expected_points, cost, is_active)
                    VALUES (?, ?, ?, ?, ?, 1)
                    ON CONFLICT(code) DO UPDATE SET
                        iso_code = excluded.iso_code,
                        name = excluded.name,
                        expected_points = excluded.expected_points,
                        cost = excluded.cost,
                        is_active = 1
                ''', [code, iso_code, name, expected_points, cost])

            db.commit()
            logger.info(f"Countries imported by {user['email']}: {len(countries_to_import)} countries")
            flash(f'Successfully imported {len(countries_to_import)} countries!', 'success')
        except sqlite3.Error as e:
            db.rollback()
            logger.error(f"Failed to import countries: {e}")
            flash('Failed to import countries.', 'error')

        return redirect(url_for('admin_countries'))

    @app.route('/admin/medals', methods=['GET', 'POST'])
    @admin_required
    def admin_medals():
        """Admin medal entry."""
        db = get_db()
        user = get_current_user()

        if request.method == 'POST':
            # Process medal updates
            updates = []
            for key, value in request.form.items():
                if key.startswith('gold_') or key.startswith('silver_') or key.startswith('bronze_'):
                    medal_type, country_code = key.split('_', 1)
                    try:
                        count = int(value) if value else 0
                        updates.append((medal_type, country_code, count))
                    except ValueError:
                        flash(f'Invalid value for {country_code} {medal_type}.', 'error')
                        return redirect(url_for('admin_medals'))

            # Group by country
            medals_by_country = {}
            for medal_type, country_code, count in updates:
                if country_code not in medals_by_country:
                    medals_by_country[country_code] = {'gold': 0, 'silver': 0, 'bronze': 0}
                medals_by_country[country_code][medal_type] = count

            # Update database
            try:
                db.execute('BEGIN')

                for country_code, medals in medals_by_country.items():
                    gold = medals['gold']
                    silver = medals['silver']
                    bronze = medals['bronze']
                    points = gold * 3 + silver * 2 + bronze

                    db.execute('''
                        INSERT INTO medals (country_code, gold, silver, bronze, points, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?)
                        ON CONFLICT(country_code) DO UPDATE SET
                            gold = excluded.gold,
                            silver = excluded.silver,
                            bronze = excluded.bronze,
                            points = excluded.points,
                            updated_at = excluded.updated_at
                    ''', [country_code, gold, silver, bronze, points, datetime.now(timezone.utc).isoformat()])

                db.commit()
                logger.info(f"Medals updated by {user['email']}: {len(medals_by_country)} countries")
                flash('Medal counts updated successfully!', 'success')
            except sqlite3.Error as e:
                db.rollback()
                logger.error(f"Failed to update medals: {e}")
                flash('Failed to update medal counts.', 'error')

            # Preserve sort parameters on redirect
            sort_by = request.args.get('sort', 'name')
            sort_order = request.args.get('order', 'asc')
            return redirect(url_for('admin_medals', sort=sort_by, order=sort_order))

        # GET request - show medal entry form with sorting
        sort_by = request.args.get('sort', 'name')
        sort_order = request.args.get('order', 'asc')

        # Validate sort parameters
        valid_sorts = ['name', 'gold', 'silver', 'bronze', 'points']
        if sort_by not in valid_sorts:
            sort_by = 'name'
        if sort_order not in ('asc', 'desc'):
            sort_order = 'asc'

        # Build ORDER BY clause
        sort_column = f'c.{sort_by}' if sort_by == 'name' else sort_by
        order_clause = f'{sort_column} {sort_order.upper()}'

        # Add secondary sort by name for stable sorting
        if sort_by != 'name':
            order_clause += ', c.name ASC'

        countries = db.execute(f'''
            SELECT c.code, c.iso_code, c.name,
                   COALESCE(m.gold, 0) as gold,
                   COALESCE(m.silver, 0) as silver,
                   COALESCE(m.bronze, 0) as bronze,
                   COALESCE(m.points, 0) as points
            FROM countries c
            LEFT JOIN medals m ON c.code = m.country_code
            WHERE c.is_active = 1
            ORDER BY {order_clause}
        ''').fetchall()

        return render_template('admin/medals.html',
                             user=user,
                             countries=countries,
                             sort_by=sort_by,
                             sort_order=sort_order)

    @app.route('/admin/medals/bulk', methods=['GET', 'POST'])
    @admin_required
    def admin_medals_bulk():
        """Admin bulk medal import - paste from Excel."""
        db = get_db()
        user = get_current_user()

        if request.method == 'POST':
            paste_data = request.form.get('paste_data', '').strip()
            reset_unlisted = request.form.get('reset_unlisted') == '1'

            if not paste_data:
                flash('Please paste medal data.', 'error')
                return redirect(url_for('admin_medals_bulk'))

            # Parse TSV data (Excel paste format)
            try:
                lines = paste_data.strip().split('\n')
                if len(lines) < 2:
                    flash('Data must include at least a header row and one data row.', 'error')
                    return redirect(url_for('admin_medals_bulk'))

                # Parse header
                header = [col.strip().lower() for col in lines[0].split('\t')]

                # Validate header - be flexible with column names
                country_idx = None
                gold_idx = None
                silver_idx = None
                bronze_idx = None

                for i, col in enumerate(header):
                    if 'country' in col or 'nation' in col:
                        country_idx = i
                    elif 'gold' in col:
                        gold_idx = i
                    elif 'silver' in col:
                        silver_idx = i
                    elif 'bronze' in col:
                        bronze_idx = i

                if country_idx is None or gold_idx is None or silver_idx is None or bronze_idx is None:
                    flash('Could not find required columns. Make sure your data includes: Country, Gold, Silver, Bronze', 'error')
                    return redirect(url_for('admin_medals_bulk'))

                # Parse data rows
                updates = []
                unmatched_countries = []

                for line_num, line in enumerate(lines[1:], start=2):
                    if not line.strip():
                        continue

                    cells = line.split('\t')
                    if len(cells) <= max(country_idx, gold_idx, silver_idx, bronze_idx):
                        flash(f'Line {line_num}: Not enough columns.', 'error')
                        return redirect(url_for('admin_medals_bulk'))

                    country_name = cells[country_idx].strip()
                    try:
                        gold = int(cells[gold_idx].strip() or 0)
                        silver = int(cells[silver_idx].strip() or 0)
                        bronze = int(cells[bronze_idx].strip() or 0)
                    except (ValueError, IndexError):
                        flash(f'Line {line_num}: Invalid medal counts for {country_name}.', 'error')
                        return redirect(url_for('admin_medals_bulk'))

                    # Look up country in database (case-insensitive match)
                    country = db.execute('''
                        SELECT code FROM countries
                        WHERE LOWER(name) = ? OR LOWER(code) = ?
                    ''', [country_name.lower(), country_name.lower()]).fetchone()

                    if not country:
                        unmatched_countries.append(country_name)
                        continue

                    updates.append((country['code'], gold, silver, bronze))

                if not updates:
                    flash('No matching countries found in your paste.', 'error')
                    return redirect(url_for('admin_medals_bulk'))

                # Update database
                try:
                    db.execute('BEGIN')

                    # Reset unlisted countries if requested
                    if reset_unlisted:
                        updated_codes = [code for code, _, _, _ in updates]
                        placeholders = ','.join('?' * len(updated_codes))
                        db.execute(f'''
                            UPDATE medals
                            SET gold = 0, silver = 0, bronze = 0, points = 0, updated_at = ?
                            WHERE country_code NOT IN ({placeholders})
                        ''', [datetime.now(timezone.utc).isoformat()] + updated_codes)

                    # Update matched countries
                    for country_code, gold, silver, bronze in updates:
                        points = gold * 3 + silver * 2 + bronze
                        db.execute('''
                            INSERT INTO medals (country_code, gold, silver, bronze, points, updated_at)
                            VALUES (?, ?, ?, ?, ?, ?)
                            ON CONFLICT(country_code) DO UPDATE SET
                                gold = excluded.gold,
                                silver = excluded.silver,
                                bronze = excluded.bronze,
                                points = excluded.points,
                                updated_at = excluded.updated_at
                        ''', [country_code, gold, silver, bronze, points, datetime.now(timezone.utc).isoformat()])

                    db.commit()

                    # Success message
                    success_msg = f'Successfully updated {len(updates)} countries!'
                    if unmatched_countries:
                        success_msg += f' Note: {len(unmatched_countries)} countries not matched: {", ".join(unmatched_countries[:5])}'
                        if len(unmatched_countries) > 5:
                            success_msg += f' and {len(unmatched_countries) - 5} more'

                    logger.info(f"Bulk medals imported by {user['email']}: {len(updates)} countries updated")
                    flash(success_msg, 'success')

                except sqlite3.Error as e:
                    db.rollback()
                    logger.error(f"Failed to bulk import medals: {e}")
                    flash('Failed to import medal data.', 'error')
                    return redirect(url_for('admin_medals_bulk'))

                return redirect(url_for('admin_medals'))

            except Exception as e:
                logger.error(f"Error parsing bulk medal data: {e}")
                flash(f'Error parsing data: {str(e)}', 'error')
                return redirect(url_for('admin_medals_bulk'))

        # GET request - show form
        return render_template('admin/medals_bulk.html', user=user)

    @app.route('/admin/users')
    @admin_required
    def admin_users():
        """Admin user management - view all users."""
        db = get_db()
        user = get_current_user()

        # Get all users with pick counts
        users = db.execute('''
            SELECT u.id, u.email, u.name, u.team_name, u.created_at,
                   COUNT(p.id) as pick_count
            FROM users u
            LEFT JOIN picks p ON u.id = p.user_id
            GROUP BY u.id
            ORDER BY u.created_at DESC
        ''').fetchall()

        admin_emails = app.config.get('ADMIN_EMAILS', [])

        return render_template('admin/users.html', user=user, users=users, admin_emails=admin_emails)

    @app.route('/admin/users/<int:user_id>/delete', methods=['POST'])
    @admin_required
    def admin_user_delete(user_id):
        """Delete a user and their picks."""
        db = get_db()
        current = get_current_user()

        # Check if user exists
        target_user = db.execute('SELECT * FROM users WHERE id = ?', [user_id]).fetchone()
        if not target_user:
            flash('User not found.', 'error')
            return redirect(url_for('admin_users'))

        # Prevent deleting yourself
        if target_user['id'] == current['id']:
            flash('You cannot delete your own account.', 'error')
            return redirect(url_for('admin_users'))

        # Delete user (CASCADE will delete picks automatically)
        try:
            db.execute('DELETE FROM users WHERE id = ?', [user_id])
            db.commit()
            logger.info(f"User deleted by {current['email']}: {target_user['email']}")
            flash(f'User {target_user["name"]} ({target_user["email"]}) deleted successfully.', 'success')
        except sqlite3.Error as e:
            db.rollback()
            logger.error(f"Failed to delete user {user_id}: {e}")
            flash('Failed to delete user.', 'error')

        return redirect(url_for('admin_users'))
