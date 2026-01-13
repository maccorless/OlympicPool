"""
Leaderboard routes - TODO: Implement in step 4
"""
from flask import abort


def register_routes(app):
    """Register leaderboard routes with Flask app."""

    @app.route('/leaderboard')
    def leaderboard():
        """Leaderboard - not implemented yet."""
        abort(501, "Leaderboard not implemented yet")

    @app.route('/team/<int:user_id>')
    def team_detail(user_id):
        """Team detail - not implemented yet."""
        abort(501, "Team detail not implemented yet")
