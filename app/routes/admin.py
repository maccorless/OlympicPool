"""
Admin routes - TODO: Implement in step 5
"""
from flask import abort


def register_routes(app):
    """Register admin routes with Flask app."""

    @app.route('/admin')
    def admin_dashboard():
        """Admin dashboard - not implemented yet."""
        abort(501, "Admin dashboard not implemented yet")

    @app.route('/admin/contest')
    def admin_contest():
        """Admin contest config - not implemented yet."""
        abort(501, "Admin contest not implemented yet")

    @app.route('/admin/countries')
    def admin_countries():
        """Admin countries - not implemented yet."""
        abort(501, "Admin countries not implemented yet")

    @app.route('/admin/medals')
    def admin_medals():
        """Admin medals - not implemented yet."""
        abort(501, "Admin medals not implemented yet")

    @app.route('/admin/users')
    def admin_users():
        """Admin users - not implemented yet."""
        abort(501, "Admin users not implemented yet")
