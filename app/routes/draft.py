"""
Draft picker routes: display countries, select picks, submit final draft.
"""
import sqlite3
import logging
from flask import render_template, request, redirect, url_for, flash, g
from app.db import get_db
from app.decorators import login_required, require_state, get_current_user, require_contest_context

logger = logging.getLogger(__name__)


def register_routes(app):
    """Register draft routes with Flask app."""

    @app.route('/<event_slug>/<contest_slug>/draft')
    @login_required
    @require_contest_context
    @require_state('open')
    def draft(event_slug, contest_slug):
        """Draft picker page - select countries within budget."""
        db = get_db()
        user = get_current_user()

        # Get contest config from g.contest
        budget = g.contest['budget']
        max_countries = g.contest['max_countries']

        # Get all active countries for this event, sorted by cost (descending)
        countries_rows = db.execute('''
            SELECT code, iso_code, name, expected_points, cost
            FROM countries
            WHERE event_id = ? AND is_active = 1
            ORDER BY cost DESC, name ASC
        ''', [g.contest['event_id']]).fetchall()

        # Convert Row objects to dicts for JSON serialization
        countries = [dict(c) for c in countries_rows]

        # Get user's current picks for this contest
        existing_picks = db.execute('''
            SELECT country_code FROM picks
            WHERE user_id = ? AND contest_id = ?
        ''', [user['id'], g.contest['id']]).fetchall()

        selected_codes = [p['country_code'] for p in existing_picks]

        return render_template('draft/picker.html',
                             countries=countries,
                             selected_codes=selected_codes,
                             budget=budget,
                             max_countries=max_countries)

    @app.route('/<event_slug>/<contest_slug>/draft/submit', methods=['POST'])
    @login_required
    @require_contest_context
    @require_state('open')
    def submit_draft(event_slug, contest_slug):
        """Submit final picks."""
        db = get_db()
        user = get_current_user()

        # Get selected countries from form
        country_codes = request.form.getlist('countries[]')

        # Validate picks
        valid, error_msg = validate_picks(country_codes)

        if not valid:
            flash(error_msg, 'error')
            return redirect(url_for('draft', event_slug=event_slug, contest_slug=contest_slug))

        # Save picks (replace existing for this contest)
        try:
            db.execute('BEGIN')

            # Delete existing picks for this contest
            db.execute('DELETE FROM picks WHERE user_id = ? AND contest_id = ?',
                     [user['id'], g.contest['id']])

            # Insert new picks with contest_id and event_id
            for code in country_codes:
                db.execute('''
                    INSERT INTO picks (user_id, contest_id, event_id, country_code)
                    VALUES (?, ?, ?, ?)
                ''', [user['id'], g.contest['id'], g.contest['event_id'], code])

            db.commit()

            flash('Your picks have been saved!', 'success')
            return redirect(url_for('my_picks', event_slug=event_slug, contest_slug=contest_slug))

        except sqlite3.Error as e:
            db.rollback()
            logger.error(f"Failed to save picks for user {user['id']}: {e}")
            flash('Failed to save picks. Please try again.', 'error')
            return redirect(url_for('draft', event_slug=event_slug, contest_slug=contest_slug))

    @app.route('/<event_slug>/<contest_slug>/my-picks')
    @login_required
    @require_contest_context
    def my_picks(event_slug, contest_slug):
        """View user's submitted picks."""
        db = get_db()
        user = get_current_user()

        # Get contest config from g.contest
        budget = g.contest['budget']
        contest_state = g.contest['state']

        # Get user's picks with country details for this contest
        picks = db.execute('''
            SELECT c.code, c.iso_code, c.name, c.cost, c.expected_points,
                   COALESCE(m.gold, 0) as gold,
                   COALESCE(m.silver, 0) as silver,
                   COALESCE(m.bronze, 0) as bronze,
                   COALESCE(m.points, 0) as points
            FROM picks p
            JOIN countries c ON p.country_code = c.code AND p.event_id = c.event_id
            LEFT JOIN medals m ON c.code = m.country_code AND m.event_id = c.event_id
            WHERE p.user_id = ? AND p.contest_id = ?
            ORDER BY c.cost DESC
        ''', [user['id'], g.contest['id']]).fetchall()

        # Calculate totals
        total_cost = sum(p['cost'] for p in picks)
        total_points = sum(p['points'] for p in picks)

        return render_template('draft/my_picks.html',
                             picks=picks,
                             total_cost=total_cost,
                             total_points=total_points,
                             budget=budget,
                             contest_state=contest_state,
                             user=user)


def validate_picks(country_codes):
    """
    Validate draft picks server-side.
    Returns (success: bool, error_message: str or None)
    """
    db = get_db()

    # Get contest config from g.contest
    budget = g.contest['budget']
    max_countries = g.contest['max_countries']

    # Check count
    if len(country_codes) == 0:
        return False, "You must select at least one country."

    if len(country_codes) > max_countries:
        return False, f"Maximum {max_countries} countries allowed."

    # Check for duplicates
    if len(country_codes) != len(set(country_codes)):
        return False, "Duplicate countries are not allowed."

    # Check that all countries exist and are active for this event
    if len(country_codes) > 0:
        placeholders = ','.join('?' * len(country_codes))

        # Verify all submitted codes are active countries for this event
        active_count = db.execute(
            f'SELECT COUNT(*) as count FROM countries WHERE event_id = ? AND is_active = 1 AND code IN ({placeholders})',
            [g.contest['event_id']] + country_codes
        ).fetchone()['count']

        if active_count != len(country_codes):
            return False, "One or more selected countries are invalid or inactive."

        # Check budget
        result = db.execute(
            f'SELECT SUM(cost) as total FROM countries WHERE event_id = ? AND is_active = 1 AND code IN ({placeholders})',
            [g.contest['event_id']] + country_codes
        ).fetchone()

        total_cost = result['total'] or 0

        if total_cost > budget:
            return False, f"Total cost ({total_cost}) exceeds budget ({budget})."

    return True, None
