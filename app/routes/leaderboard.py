"""
Leaderboard routes: public leaderboard and team detail views.
"""
import logging
from flask import render_template, abort, request, g
from app.db import get_db
from app.decorators import get_current_user, require_contest_context

logger = logging.getLogger(__name__)


def register_routes(app):
    """Register leaderboard routes with Flask app."""

    @app.route('/<event_slug>/<contest_slug>/leaderboard')
    @require_contest_context
    def leaderboard(event_slug, contest_slug):
        """Public leaderboard - visible in open/locked/complete states."""
        db = get_db()
        current_user = get_current_user()

        # Get contest state from g.contest
        contest_state = g.contest['state']

        # Only show leaderboard in open, locked, or complete states (not setup)
        if contest_state == 'setup':
            abort(404)

        # Get sort parameters (default: points DESC)
        sort_by = request.args.get('sort', 'points')
        sort_order = request.args.get('order', 'desc')

        # Validate sort parameters
        valid_sorts = ['points', 'gold', 'silver', 'bronze', 'team_name']
        if sort_by not in valid_sorts:
            sort_by = 'points'
        if sort_order not in ('asc', 'desc'):
            sort_order = 'desc'

        # Build ORDER BY clause with team_name as final tiebreaker for display order
        # NOTE: Using f-string for ORDER BY is safe here because sort_by is validated
        # against a whitelist above (valid_sorts). Dynamic ORDER BY cannot use
        # parameterized queries in SQLite.
        if sort_by == 'team_name':
            order_clause = f'u.team_name {sort_order.upper()}'
        else:
            # For medal sorting, use tiebreaker logic + team_name for stable sort
            if sort_order == 'desc':
                order_clause = f'''
                    total_{sort_by} DESC,
                    total_points DESC,
                    total_gold DESC,
                    total_silver DESC,
                    total_bronze DESC,
                    u.team_name ASC
                '''
            else:
                order_clause = f'''
                    total_{sort_by} ASC,
                    total_points ASC,
                    total_gold ASC,
                    total_silver ASC,
                    total_bronze ASC,
                    u.team_name ASC
                '''

        # Get leaderboard data (filtered by contest_id)
        teams = db.execute(f'''
            SELECT
                u.id,
                u.name,
                u.team_name,
                COALESCE(SUM(m.gold), 0) as total_gold,
                COALESCE(SUM(m.silver), 0) as total_silver,
                COALESCE(SUM(m.bronze), 0) as total_bronze,
                COALESCE(SUM(m.points), 0) as total_points
            FROM user_contest_info uci
            JOIN users u ON uci.user_id = u.id
            JOIN picks p ON u.id = p.user_id AND p.contest_id = uci.contest_id
            LEFT JOIN medals m ON p.country_code = m.country_code AND m.event_id = p.event_id
            WHERE uci.contest_id = ?
            GROUP BY u.id
            ORDER BY {order_clause}
        ''', [g.contest['id']]).fetchall()

        # First, calculate ranks based on standard tiebreaker (always points-based)
        # We need to sort by points temporarily to calculate correct ranks
        teams_for_ranking = sorted(
            [dict(t) for t in teams],
            key=lambda x: (x['total_points'], x['total_gold'], x['total_silver'], x['total_bronze']),
            reverse=True
        )

        # Assign ranks
        rank_map = {}
        current_rank = 1
        prev_scores = None

        for i, team in enumerate(teams_for_ranking):
            current_scores = (
                team['total_points'],
                team['total_gold'],
                team['total_silver'],
                team['total_bronze']
            )

            if prev_scores is not None and current_scores != prev_scores:
                current_rank = i + 1

            rank_map[team['id']] = current_rank
            prev_scores = current_scores

        # Fetch all countries for all teams in a single query (avoid N+1)
        user_ids = [team['id'] for team in teams]
        if user_ids:
            placeholders = ','.join('?' * len(user_ids))
            all_countries = db.execute(f'''
                SELECT p.user_id, c.code, c.iso_code, c.name
                FROM picks p
                JOIN countries c ON p.country_code = c.code AND p.event_id = c.event_id
                WHERE p.contest_id = ? AND p.user_id IN ({placeholders})
                ORDER BY p.user_id, c.name
            ''', [g.contest['id']] + user_ids).fetchall()

            # Group countries by user_id
            countries_by_user = {}
            for row in all_countries:
                user_id = row['user_id']
                if user_id not in countries_by_user:
                    countries_by_user[user_id] = []
                countries_by_user[user_id].append({
                    'code': row['code'],
                    'iso_code': row['iso_code'],
                    'name': row['name']
                })
        else:
            countries_by_user = {}

        # Now build teams_list with pre-fetched countries
        teams_list = []
        for team in teams:
            team_dict = dict(team)
            team_dict['countries'] = countries_by_user.get(team['id'], [])

            # In 'open' state, everyone is tied at rank 1 (games haven't started)
            # In 'locked'/'complete' states, use calculated ranks
            if contest_state == 'open':
                team_dict['rank'] = 1
                team_dict['is_tied'] = True  # Flag for "1=" display
            else:
                team_dict['rank'] = rank_map[team['id']]
                # Check if this rank is tied with next/previous team
                team_dict['is_tied'] = sum(1 for t in rank_map.values() if t == rank_map[team['id']]) > 1

            teams_list.append(team_dict)

        # Get last updated timestamp from medals table for this event
        last_update = db.execute('''
            SELECT MAX(updated_at) as last_updated FROM medals WHERE event_id = ?
        ''', [g.contest['event_id']]).fetchone()

        return render_template('leaderboard/index.html',
                             teams=teams_list,
                             contest_state=contest_state,
                             sort_by=sort_by,
                             sort_order=sort_order,
                             last_updated=last_update['last_updated'] if last_update else None,
                             current_user_id=current_user['id'] if current_user else None)

    @app.route('/<event_slug>/<contest_slug>/team/<int:user_id>')
    @require_contest_context
    def team_detail(event_slug, contest_slug, user_id):
        """View a specific team's picks and points breakdown."""
        db = get_db()

        # Get contest config from g.contest
        contest_state = g.contest['state']
        budget = g.contest['budget']

        # Only show team details in open, locked, or complete states (not setup)
        if contest_state == 'setup':
            abort(404)

        # Get user info (team_name from users table, global across contests)
        # Verify user is in this contest via user_contest_info
        user = db.execute('''
            SELECT u.id, u.name, u.team_name
            FROM users u
            JOIN user_contest_info uci ON u.id = uci.user_id
            WHERE u.id = ? AND uci.contest_id = ?
        ''', [user_id, g.contest['id']]).fetchone()

        if not user:
            abort(404)

        # Get user's picks with medal data for this contest
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
        ''', [user_id, g.contest['id']]).fetchall()

        # Calculate totals
        total_cost = sum(p['cost'] for p in picks)
        total_gold = sum(p['gold'] for p in picks)
        total_silver = sum(p['silver'] for p in picks)
        total_bronze = sum(p['bronze'] for p in picks)
        total_points = sum(p['points'] for p in picks)

        return render_template('leaderboard/team.html',
                             user=user,
                             picks=picks,
                             total_cost=total_cost,
                             total_gold=total_gold,
                             total_silver=total_silver,
                             total_bronze=total_bronze,
                             total_points=total_points,
                             budget=budget,
                             contest_state=contest_state)
