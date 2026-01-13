"""
Draft routes - TODO: Implement in step 3
"""
from flask import render_template, abort


def register_routes(app):
    """Register draft routes with Flask app."""

    @app.route('/draft')
    def draft():
        """Draft picker - not implemented yet."""
        abort(501, "Draft picker not implemented yet")

    @app.route('/my-picks')
    def my_picks():
        """View own picks - not implemented yet."""
        abort(501, "My picks not implemented yet")
