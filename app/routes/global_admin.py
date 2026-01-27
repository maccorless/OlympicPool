"""
Global admin routes for managing events and contests.

These routes are separate from contest-specific admin routes and require
GLOBAL_ADMIN_EMAILS authorization.
"""
import sqlite3
import logging
from datetime import datetime, timezone
from flask import render_template, request, redirect, url_for, flash, current_app
from app.db import get_db
from app.decorators import get_current_user, global_admin_required

logger = logging.getLogger(__name__)


def register_routes(app):
    """Register global admin routes with Flask app."""

    @app.route('/admin/global')
    @global_admin_required
    def global_admin_dashboard():
        """Global admin dashboard - unified hierarchical interface."""
        db = get_db()
        user = get_current_user()

        # Get all events with contest counts
        events = db.execute('''
            SELECT e.*,
                   COUNT(DISTINCT c.id) as contest_count,
                   COUNT(DISTINCT uci.user_id) as total_users
            FROM events e
            LEFT JOIN contest c ON e.id = c.event_id
            LEFT JOIN user_contest_info uci ON c.id = uci.contest_id
            GROUP BY e.id
            ORDER BY e.start_date DESC
        ''').fetchall()

        # Get all contests in single query (avoid N+1)
        all_contests = db.execute('''
            SELECT c.*,
                   e.id as event_id,
                   e.slug as event_slug,
                   COUNT(DISTINCT uci.user_id) as user_count,
                   COUNT(DISTINCT p.id) as pick_count
            FROM contest c
            JOIN events e ON c.event_id = e.id
            LEFT JOIN user_contest_info uci ON c.id = uci.contest_id
            LEFT JOIN picks p ON c.id = p.contest_id
            GROUP BY c.id
            ORDER BY c.created_at DESC
        ''').fetchall()

        # Group contests by event_id in Python
        contests_by_event = {}
        for contest in all_contests:
            event_id = contest['event_id']
            if event_id not in contests_by_event:
                contests_by_event[event_id] = []
            contests_by_event[event_id].append(dict(contest))

        # Get total system stats
        stats = {
            'total_events': len(events),
            'total_contests': db.execute('SELECT COUNT(*) as count FROM contest').fetchone()['count'],
            'total_users': db.execute('SELECT COUNT(*) as count FROM users').fetchone()['count'],
            'total_countries': db.execute('SELECT COUNT(DISTINCT code) as count FROM countries').fetchone()['count']
        }

        # Use request.url_root for shareable URLs (works with any port/domain)
        base_url = request.url_root.rstrip('/')

        return render_template('admin/global/dashboard.html',
                             user=user,
                             events=[dict(e) for e in events],
                             contests_by_event=contests_by_event,
                             stats=stats,
                             base_url=base_url)

    @app.route('/admin/global/events/create', methods=['GET', 'POST'])
    @global_admin_required
    def global_admin_event_create():
        """Create a new event."""
        db = get_db()
        user = get_current_user()

        if request.method == 'POST':
            name = request.form.get('name', '').strip()
            slug = request.form.get('slug', '').strip()
            description = request.form.get('description', '').strip()
            start_date = request.form.get('start_date', '').strip()
            end_date = request.form.get('end_date', '').strip()
            is_active = 1 if request.form.get('is_active') == 'on' else 0

            # Validation
            if not all([name, slug, start_date, end_date]):
                flash('Name, slug, start date, and end date are required.', 'error')
                return render_template('admin/global/event_form.html', user=user, event=None)

            # Validate slug format (lowercase, hyphens, numbers only)
            if not all(c.islower() or c.isdigit() or c == '-' for c in slug):
                flash('Slug must be lowercase with hyphens and numbers only (e.g., "milano-2026").', 'error')
                return render_template('admin/global/event_form.html', user=user, event=None)

            # Check if slug already exists
            existing = db.execute('SELECT id FROM events WHERE slug = ?', [slug]).fetchone()
            if existing:
                flash(f'Event with slug "{slug}" already exists.', 'error')
                return render_template('admin/global/event_form.html', user=user, event=None)

            # Create event
            try:
                db.execute('''
                    INSERT INTO events (name, slug, description, start_date, end_date, is_active)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', [name, slug, description, start_date, end_date, is_active])
                db.commit()

                logger.info(f"Event created by {user['email']}: {name} ({slug})")
                flash(f'Event "{name}" created successfully!', 'success')
                return redirect(url_for('global_admin_dashboard'))

            except sqlite3.Error as e:
                db.rollback()
                logger.error(f"Failed to create event: {e}")
                flash('Failed to create event. Please try again.', 'error')

        breadcrumb_context = {'action': 'Create Event'}
        return render_template('admin/global/event_form.html',
                             user=user,
                             event=None,
                             breadcrumb_context=breadcrumb_context)

    @app.route('/admin/global/events/<int:event_id>/edit', methods=['GET', 'POST'])
    @global_admin_required
    def global_admin_event_edit(event_id):
        """Edit an existing event."""
        db = get_db()
        user = get_current_user()

        event = db.execute('SELECT * FROM events WHERE id = ?', [event_id]).fetchone()
        if not event:
            flash('Event not found.', 'error')
            return redirect(url_for('global_admin_events'))

        if request.method == 'POST':
            name = request.form.get('name', '').strip()
            slug = request.form.get('slug', '').strip()
            description = request.form.get('description', '').strip()
            start_date = request.form.get('start_date', '').strip()
            end_date = request.form.get('end_date', '').strip()
            is_active = 1 if request.form.get('is_active') == 'on' else 0

            # Validation
            if not all([name, slug, start_date, end_date]):
                flash('Name, slug, start date, and end date are required.', 'error')
                return render_template('admin/global/event_form.html', user=user, event=event)

            # Validate slug format
            if not all(c.islower() or c.isdigit() or c == '-' for c in slug):
                flash('Slug must be lowercase with hyphens and numbers only.', 'error')
                return render_template('admin/global/event_form.html', user=user, event=event)

            # Check if slug already exists (but not for this event)
            existing = db.execute('SELECT id FROM events WHERE slug = ? AND id != ?', [slug, event_id]).fetchone()
            if existing:
                flash(f'Event with slug "{slug}" already exists.', 'error')
                return render_template('admin/global/event_form.html', user=user, event=event)

            # Update event
            try:
                db.execute('''
                    UPDATE events
                    SET name = ?, slug = ?, description = ?, start_date = ?, end_date = ?, is_active = ?,
                        updated_at = ?
                    WHERE id = ?
                ''', [name, slug, description, start_date, end_date, is_active,
                      datetime.now(timezone.utc).isoformat(), event_id])
                db.commit()

                logger.info(f"Event updated by {user['email']}: {name} ({slug})")
                flash(f'Event "{name}" updated successfully!', 'success')
                return redirect(url_for('global_admin_dashboard'))

            except sqlite3.Error as e:
                db.rollback()
                logger.error(f"Failed to update event: {e}")
                flash('Failed to update event. Please try again.', 'error')

        breadcrumb_context = {'action': 'Edit Event', 'name': event['name']}
        return render_template('admin/global/event_form.html',
                             user=user,
                             event=event,
                             breadcrumb_context=breadcrumb_context)

    @app.route('/admin/global/contests/create', methods=['GET', 'POST'])
    @global_admin_required
    def global_admin_contest_create():
        """Create a new contest."""
        db = get_db()
        user = get_current_user()

        # Get all events for dropdown
        events = db.execute('SELECT * FROM events ORDER BY start_date DESC').fetchall()

        if request.method == 'POST':
            event_id = request.form.get('event_id', '').strip()
            slug = request.form.get('slug', '').strip()
            name = request.form.get('name', '').strip()
            description = request.form.get('description', '').strip()
            state = request.form.get('state', '').strip()
            budget = request.form.get('budget', '').strip()
            max_countries = request.form.get('max_countries', '').strip()
            deadline = request.form.get('deadline', '').strip()

            # Validation
            if not all([event_id, slug, name, state, budget, max_countries, deadline]):
                flash('All required fields must be filled.', 'error')
                return render_template('admin/global/contest_form.html', user=user, contest=None, events=events)

            try:
                event_id = int(event_id)
                budget = int(budget)
                max_countries = int(max_countries)
            except ValueError:
                flash('Event ID, budget, and max countries must be integers.', 'error')
                return render_template('admin/global/contest_form.html', user=user, contest=None, events=events)

            # Validate slug format
            if not all(c.islower() or c.isdigit() or c == '-' for c in slug):
                flash('Slug must be lowercase with hyphens and numbers only (e.g., "office-pool").', 'error')
                return render_template('admin/global/contest_form.html', user=user, contest=None, events=events)

            # Check if slug already exists for this event
            existing = db.execute(
                'SELECT id FROM contest WHERE event_id = ? AND slug = ?',
                [event_id, slug]
            ).fetchone()
            if existing:
                flash(f'Contest with slug "{slug}" already exists for this event.', 'error')
                return render_template('admin/global/contest_form.html', user=user, contest=None, events=events)

            # Validate state
            if state not in ('setup', 'open', 'locked', 'complete'):
                flash('Invalid contest state.', 'error')
                return render_template('admin/global/contest_form.html', user=user, contest=None, events=events)

            # Format deadline
            if len(deadline) == 16:  # YYYY-MM-DDTHH:MM
                deadline = deadline + ':00Z'
            elif not deadline.endswith('Z'):
                deadline = deadline + 'Z'

            # Create contest
            try:
                db.execute('''
                    INSERT INTO contest (event_id, slug, name, description, state, budget, max_countries, deadline)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', [event_id, slug, name, description, state, budget, max_countries, deadline])
                db.commit()

                logger.info(f"Contest created by {user['email']}: {name} ({slug})")
                flash(f'Contest "{name}" created successfully!', 'success')
                return redirect(url_for('global_admin_dashboard'))

            except sqlite3.Error as e:
                db.rollback()
                logger.error(f"Failed to create contest: {e}")
                flash('Failed to create contest. Please try again.', 'error')

        breadcrumb_context = {'action': 'Create Contest'}
        return render_template('admin/global/contest_form.html',
                             user=user,
                             contest=None,
                             events=events,
                             breadcrumb_context=breadcrumb_context)

    @app.route('/admin/global/contests/<int:contest_id>/edit', methods=['GET', 'POST'])
    @global_admin_required
    def global_admin_contest_edit(contest_id):
        """Edit an existing contest."""
        db = get_db()
        user = get_current_user()

        contest = db.execute('''
            SELECT c.*, e.name as event_name, e.slug as event_slug
            FROM contest c
            JOIN events e ON c.event_id = e.id
            WHERE c.id = ?
        ''', [contest_id]).fetchone()
        if not contest:
            flash('Contest not found.', 'error')
            return redirect(url_for('global_admin_dashboard'))

        # Get all events for dropdown
        events = db.execute('SELECT * FROM events ORDER BY start_date DESC').fetchall()

        if request.method == 'POST':
            event_id = request.form.get('event_id', '').strip()
            slug = request.form.get('slug', '').strip()
            name = request.form.get('name', '').strip()
            description = request.form.get('description', '').strip()
            state = request.form.get('state', '').strip()
            budget = request.form.get('budget', '').strip()
            max_countries = request.form.get('max_countries', '').strip()
            deadline = request.form.get('deadline', '').strip()

            # Validation
            if not all([event_id, slug, name, state, budget, max_countries, deadline]):
                flash('All required fields must be filled.', 'error')
                return render_template('admin/global/contest_form.html', user=user, contest=contest, events=events)

            try:
                event_id = int(event_id)
                budget = int(budget)
                max_countries = int(max_countries)
            except ValueError:
                flash('Event ID, budget, and max countries must be integers.', 'error')
                return render_template('admin/global/contest_form.html', user=user, contest=contest, events=events)

            # Validate slug format
            if not all(c.islower() or c.isdigit() or c == '-' for c in slug):
                flash('Slug must be lowercase with hyphens and numbers only.', 'error')
                return render_template('admin/global/contest_form.html', user=user, contest=contest, events=events)

            # Check if slug already exists for this event (but not for this contest)
            existing = db.execute(
                'SELECT id FROM contest WHERE event_id = ? AND slug = ? AND id != ?',
                [event_id, slug, contest_id]
            ).fetchone()
            if existing:
                flash(f'Contest with slug "{slug}" already exists for this event.', 'error')
                return render_template('admin/global/contest_form.html', user=user, contest=contest, events=events)

            # Validate state
            if state not in ('setup', 'open', 'locked', 'complete'):
                flash('Invalid contest state.', 'error')
                return render_template('admin/global/contest_form.html', user=user, contest=contest, events=events)

            # Format deadline
            if len(deadline) == 16:  # YYYY-MM-DDTHH:MM
                deadline = deadline + ':00Z'
            elif not deadline.endswith('Z'):
                deadline = deadline + 'Z'

            # Update contest
            try:
                db.execute('''
                    UPDATE contest
                    SET event_id = ?, slug = ?, name = ?, description = ?, state = ?,
                        budget = ?, max_countries = ?, deadline = ?, updated_at = ?
                    WHERE id = ?
                ''', [event_id, slug, name, description, state, budget, max_countries, deadline,
                      datetime.now(timezone.utc).isoformat(), contest_id])
                db.commit()

                logger.info(f"Contest updated by {user['email']}: {name} ({slug})")
                flash(f'Contest "{name}" updated successfully!', 'success')
                return redirect(url_for('global_admin_dashboard'))

            except sqlite3.Error as e:
                db.rollback()
                logger.error(f"Failed to update contest: {e}")
                flash('Failed to update contest. Please try again.', 'error')

        breadcrumb_context = {
            'action': 'Edit Contest',
            'name': contest['name'],
            'parent_name': contest['event_name']
        }

        # Use request.url_root for URL warning (works with any port/domain)
        base_url = request.url_root.rstrip('/')

        return render_template('admin/global/contest_form.html',
                             user=user,
                             contest=contest,
                             events=events,
                             breadcrumb_context=breadcrumb_context,
                             base_url=base_url)

    @app.route('/admin/global/events/<int:event_id>/delete', methods=['POST'])
    @global_admin_required
    def global_admin_event_delete(event_id):
        """Delete an event (CASCADE deletes all contests, users, picks, countries, medals)."""
        db = get_db()
        user = get_current_user()

        event = db.execute('SELECT * FROM events WHERE id = ?', [event_id]).fetchone()
        if not event:
            flash('Event not found.', 'error')
            return redirect(url_for('global_admin_dashboard'))

        # Get stats for confirmation
        stats = db.execute('''
            SELECT
                COUNT(DISTINCT c.id) as contest_count,
                COUNT(DISTINCT uci.user_id) as user_count,
                COUNT(DISTINCT p.id) as pick_count,
                COUNT(DISTINCT co.code) as country_count
            FROM events e
            LEFT JOIN contest c ON e.id = c.event_id
            LEFT JOIN user_contest_info uci ON c.id = uci.contest_id
            LEFT JOIN picks p ON c.id = p.contest_id
            LEFT JOIN countries co ON e.id = co.event_id
            WHERE e.id = ?
        ''', [event_id]).fetchone()

        # Check if confirmed
        confirmed = request.form.get('confirmed') == 'yes'

        if not confirmed:
            # Show confirmation page
            breadcrumb_context = {'action': 'Delete Event', 'name': event['name']}
            return render_template('admin/global/event_delete_confirm.html',
                                 user=user,
                                 event=event,
                                 stats=stats,
                                 breadcrumb_context=breadcrumb_context)

        # Delete event (CASCADE will handle related data)
        try:
            db.execute('DELETE FROM events WHERE id = ?', [event_id])
            db.commit()

            logger.warning(f"Event DELETED by {user['email']}: {event['name']} (id={event_id}) - "
                         f"{stats['contest_count']} contests, {stats['user_count']} users affected")
            flash(f'Event "{event["name"]}" deleted successfully. '
                  f'{stats["contest_count"]} contest(s) and associated data removed.', 'success')
            return redirect(url_for('global_admin_dashboard'))

        except sqlite3.Error as e:
            db.rollback()
            logger.error(f"Failed to delete event: {e}")
            flash('Failed to delete event. Please try again.', 'error')
            return redirect(url_for('global_admin_dashboard'))

    @app.route('/admin/global/contests/<int:contest_id>/delete', methods=['POST'])
    @global_admin_required
    def global_admin_contest_delete(contest_id):
        """Delete a contest (CASCADE deletes user_contest_info and picks)."""
        db = get_db()
        user = get_current_user()

        contest = db.execute('''
            SELECT c.*, e.name as event_name, e.slug as event_slug
            FROM contest c
            JOIN events e ON c.event_id = e.id
            WHERE c.id = ?
        ''', [contest_id]).fetchone()

        if not contest:
            flash('Contest not found.', 'error')
            return redirect(url_for('global_admin_dashboard'))

        # Get stats for confirmation
        stats = db.execute('''
            SELECT
                COUNT(DISTINCT uci.user_id) as user_count,
                COUNT(DISTINCT p.id) as pick_count
            FROM contest c
            LEFT JOIN user_contest_info uci ON c.id = uci.contest_id
            LEFT JOIN picks p ON c.id = p.contest_id
            WHERE c.id = ?
        ''', [contest_id]).fetchone()

        # Check if confirmed
        confirmed = request.form.get('confirmed') == 'yes'

        if not confirmed:
            # Show confirmation page
            breadcrumb_context = {'action': 'Delete Contest', 'name': contest['name']}
            return render_template('admin/global/contest_delete_confirm.html',
                                 user=user,
                                 contest=contest,
                                 stats=stats,
                                 breadcrumb_context=breadcrumb_context)

        # Delete contest (CASCADE will handle related data)
        try:
            db.execute('DELETE FROM contest WHERE id = ?', [contest_id])
            db.commit()

            logger.warning(f"Contest DELETED by {user['email']}: {contest['name']} (id={contest_id}) - "
                         f"{stats['user_count']} users, {stats['pick_count']} picks removed")
            flash(f'Contest "{contest["name"]}" deleted successfully. '
                  f'{stats["user_count"]} user registration(s) and {stats["pick_count"]} pick(s) removed.', 'success')
            return redirect(url_for('global_admin_dashboard'))

        except sqlite3.Error as e:
            db.rollback()
            logger.error(f"Failed to delete contest: {e}")
            flash('Failed to delete contest. Please try again.', 'error')
            return redirect(url_for('global_admin_dashboard'))
