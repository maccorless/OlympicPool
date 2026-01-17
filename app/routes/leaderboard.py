"""
Leaderboard routes: public leaderboard and team detail views.
"""
from flask import render_template, abort, request
from app.db import get_db
from app.decorators import get_current_user


def register_routes(app):
    """Register leaderboard routes with Flask app."""

    @app.route('/leaderboard')
    def leaderboard():
        """Public leaderboard - visible in open/locked/complete states."""
        db = get_db()
        current_user = get_current_user()

        # Get contest state
        contest = db.execute('SELECT state FROM contest WHERE id = 1').fetchone()

        # Only show leaderboard in open, locked, or complete states (not setup)
        if contest['state'] == 'setup':
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

        # Get leaderboard data
        teams = db.execute(f'''
            SELECT
                u.id,
                u.name,
                u.team_name,
                COALESCE(SUM(m.gold), 0) as total_gold,
                COALESCE(SUM(m.silver), 0) as total_silver,
                COALESCE(SUM(m.bronze), 0) as total_bronze,
                COALESCE(SUM(m.points), 0) as total_points
            FROM users u
            JOIN picks p ON u.id = p.user_id
            LEFT JOIN medals m ON p.country_code = m.country_code
            GROUP BY u.id
            ORDER BY {order_clause}
        ''').fetchall()

        # Calculate ranks based ONLY on points (and tiebreakers)
        # NOTE: Rank is ALWAYS points-based, regardless of how the table is sorted
        # This ensures consistent ranking even when users sort by name, gold medals, etc.
        #
        # Ranking tiebreaker order:
        # 1. Total points (desc)
        # 2. Gold medals (desc)
        # 3. Silver medals (desc)
        # 4. Bronze medals (desc)
        # Tied teams get same rank with "=" suffix (e.g., "2=", "2=", "4")

        teams_for_ranking = sorted(
            [dict(t) for t in teams],
            key=lambda x: (x['total_points'], x['total_gold'], x['total_silver'], x['total_bronze']),
            reverse=True
        )

        # Two-pass algorithm: (1) assign ranks, (2) detect ties and add "=" suffix
        rank_map = {}
        rank_counts = {}
        temp_ranks = []

        current_rank = 1
        prev_scores = None

        # Pass 1: Assign rank numbers based on tiebreaker order
        for i, team in enumerate(teams_for_ranking):
            current_scores = (
                team['total_points'],
                team['total_gold'],
                team['total_silver'],
                team['total_bronze']
            )

            # New score group starts a new rank
            if prev_scores is not None and current_scores != prev_scores:
                current_rank = i + 1

            temp_ranks.append((team['id'], current_rank))
            rank_counts[current_rank] = rank_counts.get(current_rank, 0) + 1
            prev_scores = current_scores

        # Pass 2: Add "=" suffix to tied ranks
        for team_id, rank_num in temp_ranks:
            if rank_counts[rank_num] > 1:
                rank_map[team_id] = f"{rank_num}="  # Multiple teams at this rank
            else:
                rank_map[team_id] = str(rank_num)    # Sole team at this rank

        # Fetch all countries for all teams in a single query (avoid N+1)
        user_ids = [team['id'] for team in teams]
        if user_ids:
            placeholders = ','.join('?' * len(user_ids))
            all_countries = db.execute(f'''
                SELECT p.user_id, c.code, c.iso_code, c.name
                FROM picks p
                JOIN countries c ON p.country_code = c.code
                WHERE p.user_id IN ({placeholders})
                ORDER BY p.user_id, c.name
            ''', user_ids).fetchall()

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
            team_dict['rank'] = rank_map[team['id']]  # Apply pre-calculated rank
            teams_list.append(team_dict)

        # Get last updated timestamp from medals table
        last_update = db.execute('''
            SELECT MAX(updated_at) as last_updated FROM medals
        ''').fetchone()

        return render_template('leaderboard/index.html',
                             teams=teams_list,
                             contest_state=contest['state'],
                             sort_by=sort_by,
                             sort_order=sort_order,
                             last_updated=last_update['last_updated'] if last_update else None,
                             current_user_id=current_user['id'] if current_user else None)

    @app.route('/team/<int:user_id>')
    def team_detail(user_id):
        """View a specific team's picks and points breakdown."""
        db = get_db()
        current_user = get_current_user()

        # Get contest state
        contest = db.execute('SELECT state, budget FROM contest WHERE id = 1').fetchone()

        # Only show team details in open, locked, or complete states (not setup)
        if contest['state'] == 'setup':
            abort(404)

        # Authorization check for 'open' state
        if contest['state'] == 'open':
            # In open mode, only allow viewing own picks or if admin
            is_own_picks = current_user and current_user['id'] == user_id
            is_admin = current_user and current_user['email'] in app.config['ADMIN_EMAILS']

            if not (is_own_picks or is_admin):
                abort(403)  # Forbidden: can't view other users' picks during open mode

        # Get user info
        user = db.execute('SELECT id, name, team_name FROM users WHERE id = ?', [user_id]).fetchone()

        if not user:
            abort(404)

        # Get user's picks with medal data
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
        ''', [user_id]).fetchall()

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
                             budget=contest['budget'],
                             contest_state=contest['state'])

    @app.route('/medals')
    def medal_table():
        """Medal table showing all countries with their medals and efficiency."""
        db = get_db()

        # Get contest state
        contest = db.execute('SELECT state FROM contest WHERE id = 1').fetchone()

        # Medal table visible in all states (setup shows 404, open/locked/complete show table)
        if contest['state'] == 'setup':
            abort(404)

        # Get sort parameters (default: points DESC)
        sort_by = request.args.get('sort', 'points')
        sort_order = request.args.get('order', 'desc')

        # Validate sort parameters
        valid_sorts = ['points', 'gold', 'silver', 'bronze', 'efficiency', 'country']
        if sort_by not in valid_sorts:
            sort_by = 'points'
        if sort_order not in ('asc', 'desc'):
            sort_order = 'desc'

        # Build ORDER BY clause
        if sort_by == 'efficiency':
            # Sort by points/cost ratio
            order_clause = f'efficiency {sort_order.upper()}, m.points DESC'
        elif sort_by == 'country':
            order_clause = f'c.name {sort_order.upper()}'
        else:
            # Sort by medal counts
            order_clause = f'm.{sort_by} {sort_order.upper()}, c.name ASC'

        # Get all countries with medal data and efficiency
        countries = db.execute(f'''
            SELECT
                c.code,
                c.iso_code,
                c.name,
                c.cost,
                COALESCE(m.gold, 0) as gold,
                COALESCE(m.silver, 0) as silver,
                COALESCE(m.bronze, 0) as bronze,
                COALESCE(m.points, 0) as points,
                CASE
                    WHEN c.cost > 0 THEN ROUND(CAST(COALESCE(m.points, 0) AS FLOAT) / c.cost, 2)
                    ELSE 0
                END as efficiency
            FROM countries c
            LEFT JOIN medals m ON c.code = m.country_code
            WHERE c.is_active = 1
            ORDER BY {order_clause}
        ''').fetchall()

        # Get last updated timestamp
        last_update = db.execute('''
            SELECT MAX(updated_at) as last_updated FROM medals
        ''').fetchone()

        return render_template('leaderboard/medals.html',
                             countries=countries,
                             sort_by=sort_by,
                             sort_order=sort_order,
                             contest_state=contest['state'],
                             last_updated=last_update['last_updated'] if last_update else None)
