"""
Draft picker routes: display countries, select picks, submit final draft.
"""
import sqlite3
import logging
from flask import render_template, request, redirect, url_for, flash, make_response, jsonify
from app.db import get_db
from app.decorators import login_required, require_state, get_current_user

logger = logging.getLogger(__name__)


def register_routes(app):
    """Register draft routes with Flask app."""

    @app.route('/draft')
    @login_required
    @require_state('open')
    def draft():
        """Draft picker page - select countries within budget."""
        db = get_db()
        user = get_current_user()

        # Get contest config
        contest = db.execute('SELECT budget, max_countries FROM contest WHERE id = 1').fetchone()

        # Get all active countries sorted by cost (descending)
        countries_rows = db.execute('''
            SELECT code, iso_code, name, expected_points, cost
            FROM countries
            WHERE is_active = 1
            ORDER BY cost DESC, name ASC
        ''').fetchall()

        # Convert Row objects to dicts for JSON serialization
        countries = [dict(c) for c in countries_rows]

        # Get user's current picks
        existing_picks = db.execute('''
            SELECT country_code FROM picks WHERE user_id = ?
        ''', [user['id']]).fetchall()

        selected_codes = [p['country_code'] for p in existing_picks]

        return render_template('draft/picker.html',
                             countries=countries,
                             selected_codes=selected_codes,
                             budget=contest['budget'],
                             max_countries=contest['max_countries'])

    @app.route('/draft/submit', methods=['POST'])
    @login_required
    @require_state('open')
    def submit_draft():
        """Submit final picks."""
        db = get_db()
        user = get_current_user()

        # Get selected countries from form
        country_codes = request.form.getlist('countries[]')

        # Validate picks
        valid, error_msg = validate_picks(country_codes)

        if not valid:
            flash(error_msg, 'error')
            return redirect(url_for('draft'))

        # Save picks (replace existing)
        try:
            db.execute('BEGIN')

            # Delete existing picks
            db.execute('DELETE FROM picks WHERE user_id = ?', [user['id']])

            # Insert new picks
            for code in country_codes:
                db.execute('''
                    INSERT INTO picks (user_id, country_code)
                    VALUES (?, ?)
                ''', [user['id'], code])

            db.commit()

            flash('Your picks have been saved!', 'success')
            return redirect(url_for('my_picks'))

        except sqlite3.Error as e:
            db.rollback()
            logger.error(f"Failed to save picks for user {user['id']}: {e}")
            flash('Failed to save picks. Please try again.', 'error')
            return redirect(url_for('draft'))

    @app.route('/my-picks')
    @login_required
    def my_picks():
        """View user's submitted picks."""
        db = get_db()
        user = get_current_user()

        # Get contest state
        contest = db.execute('SELECT state, budget FROM contest WHERE id = 1').fetchone()

        # Get user's picks with country details
        picks = db.execute('''
            SELECT c.code, c.iso_code, c.name, c.cost, c.expected_points,
                   COALESCE(m.gold, 0) as gold,
                   COALESCE(m.silver, 0) as silver,
                   COALESCE(m.bronze, 0) as bronze,
                   COALESCE(m.points, 0) as points
            FROM picks p
            JOIN countries c ON p.country_code = c.code
            LEFT JOIN medals m ON c.code = m.country_code
            WHERE p.user_id = ?
            ORDER BY c.cost DESC
        ''', [user['id']]).fetchall()

        # Calculate totals
        total_cost = sum(p['cost'] for p in picks)
        total_points = sum(p['points'] for p in picks)

        return render_template('draft/my_picks.html',
                             picks=picks,
                             total_cost=total_cost,
                             total_points=total_points,
                             budget=contest['budget'],
                             contest_state=contest['state'],
                             user=user)


def validate_picks(country_codes):
    """
    Validate draft picks server-side.
    Returns (success: bool, error_message: str or None)
    """
    db = get_db()

    # Get contest config
    contest = db.execute('SELECT budget, max_countries, state FROM contest WHERE id = 1').fetchone()

    # Check contest state (redundant with @require_state but defensive)
    if contest['state'] != 'open':
        return False, "Contest is not open for picks."

    # Check count
    if len(country_codes) == 0:
        return False, "You must select at least one country."

    if len(country_codes) > contest['max_countries']:
        return False, f"Maximum {contest['max_countries']} countries allowed."

    # Check for duplicates
    if len(country_codes) != len(set(country_codes)):
        return False, "Duplicate countries are not allowed."

    # Check budget
    if len(country_codes) > 0:
        placeholders = ','.join('?' * len(country_codes))
        result = db.execute(
            f'SELECT SUM(cost) as total FROM countries WHERE code IN ({placeholders})',
            country_codes
        ).fetchone()

        total_cost = result['total'] or 0

        if total_cost > contest['budget']:
            return False, f"Total cost ({total_cost}) exceeds budget ({contest['budget']})."

    return True, None
