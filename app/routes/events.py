"""
Event and contest selection routes.
"""
from flask import render_template, redirect, url_for
from app.db import get_db
from app.decorators import get_current_user


def register_routes(app):
    """Register event/contest selection routes with Flask app."""

    @app.route('/')
    def contest_selector():
        """
        Show list of all active contests grouped by event.

        Smart redirect logic:
        - If only ONE active contest exists in system
        - AND user is logged in and registered for that contest
        - THEN redirect to /<event_slug>/<contest_slug>
        - ELSE show contest selector page
        """
        db = get_db()
        user = get_current_user()

        # Get all active contests with event info
        active_contests = db.execute('''
            SELECT
                c.id,
                c.slug as contest_slug,
                c.name as contest_name,
                c.description,
                c.state,
                e.slug as event_slug,
                e.name as event_name
            FROM contest c
            JOIN events e ON c.event_id = e.id
            WHERE e.is_active = 1
            ORDER BY e.start_date DESC, c.name ASC
        ''').fetchall()

        # Smart redirect: if only one contest and user is registered
        if len(active_contests) == 1 and user:
            contest = active_contests[0]

            # Check if user is registered for this contest
            registered = db.execute('''
                SELECT 1 FROM user_contest_info
                WHERE user_id = ? AND contest_id = ?
            ''', [user['id'], contest['id']]).fetchone()

            if registered:
                return redirect(url_for('contest_home',
                                      event_slug=contest['event_slug'],
                                      contest_slug=contest['contest_slug']))

        # Show contest selector
        # Group contests by event
        contests_by_event = {}
        for contest in active_contests:
            event_name = contest['event_name']
            if event_name not in contests_by_event:
                contests_by_event[event_name] = []
            contests_by_event[event_name].append(contest)

        # Get user's contests if logged in
        user_contests = []
        if user:
            user_contests = db.execute('''
                SELECT
                    c.id,
                    c.slug as contest_slug,
                    c.name as contest_name,
                    c.description,
                    c.state,
                    e.slug as event_slug,
                    e.name as event_name
                FROM user_contest_info uci
                JOIN contest c ON uci.contest_id = c.id
                JOIN events e ON c.event_id = e.id
                WHERE uci.user_id = ?
                ORDER BY e.start_date DESC, c.name ASC
            ''', [user['id']]).fetchall()

        return render_template('events/contest_selector.html',
                             contests_by_event=contests_by_event,
                             user_contests=user_contests)

    @app.route('/<event_slug>/<contest_slug>')
    def contest_home(event_slug, contest_slug):
        """
        Contest landing page.
        - Shows landing page with contest info and how to play for non-authenticated users
        - Redirects to appropriate page (draft/leaderboard) for registered users
        """
        from app.decorators import require_contest_context

        # Manually load contest context (we're not using decorator here)
        from app.decorators import get_contest_from_url
        contest = get_contest_from_url()

        if not contest:
            return redirect(url_for('contest_selector'))

        event = contest['event']
        user = get_current_user()

        # If not logged in, show landing page
        if not user:
            return render_template('events/contest_landing.html',
                                 contest=contest,
                                 event=event)

        # Check if user is registered for this contest
        db = get_db()
        registered = db.execute('''
            SELECT 1 FROM user_contest_info
            WHERE user_id = ? AND contest_id = ?
        ''', [user['id'], contest['id']]).fetchone()

        # Not registered - show landing page with option to register
        if not registered:
            return render_template('events/contest_landing.html',
                                 contest=contest,
                                 event=event)

        # Registered user - show appropriate page based on contest state
        state = contest['state']

        if state == 'setup':
            # Contest not yet open - show landing page
            return render_template('events/contest_landing.html',
                                 contest=contest,
                                 event=event)
        elif state == 'open':
            # Redirect to draft picker
            return redirect(url_for('draft', event_slug=event_slug, contest_slug=contest_slug))
        else:
            # locked or complete - redirect to leaderboard
            return redirect(url_for('leaderboard', event_slug=event_slug, contest_slug=contest_slug))
