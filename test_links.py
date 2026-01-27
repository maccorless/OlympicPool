#!/usr/bin/env python3
"""
Test all links in the global admin interface.
"""
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app

def test_all_routes():
    """Test that all global admin routes are registered."""
    print("\n" + "="*70)
    print("TESTING GLOBAL ADMIN ROUTE REGISTRATION")
    print("="*70)

    app = create_app()

    # Get all registered routes
    routes = []
    for rule in app.url_map.iter_rules():
        routes.append((rule.rule, rule.endpoint))

    # Check for global admin routes
    global_admin_routes = [
        ('/admin/global', 'global_admin_dashboard'),
        ('/admin/global/events', 'global_admin_events'),
        ('/admin/global/events/create', 'global_admin_event_create'),
        ('/admin/global/events/<int:event_id>/edit', 'global_admin_event_edit'),
        ('/admin/global/events/<int:event_id>/delete', 'global_admin_event_delete'),
        ('/admin/global/contests', 'global_admin_contests'),
        ('/admin/global/contests/create', 'global_admin_contest_create'),
        ('/admin/global/contests/<int:contest_id>/edit', 'global_admin_contest_edit'),
        ('/admin/global/contests/<int:contest_id>/delete', 'global_admin_contest_delete'),
    ]

    print("\nChecking route registration:")
    all_good = True

    for path, endpoint in global_admin_routes:
        # Find the route
        found = False
        for route_path, route_endpoint in routes:
            if route_endpoint == endpoint:
                found = True
                if route_path == path:
                    print(f"✅ {endpoint:40s} → {path}")
                else:
                    print(f"⚠️  {endpoint:40s} → Expected: {path}, Got: {route_path}")
                break

        if not found:
            print(f"❌ {endpoint:40s} → NOT REGISTERED")
            all_good = False

    # Check base.html link
    print("\n" + "="*70)
    print("CHECKING NAVIGATION LINKS")
    print("="*70)

    with app.app_context():
        from flask import url_for

        try:
            url = url_for('global_admin_dashboard')
            print(f"✅ url_for('global_admin_dashboard') → {url}")
        except Exception as e:
            print(f"❌ url_for('global_admin_dashboard') → ERROR: {e}")
            all_good = False

        try:
            url = url_for('global_admin_events')
            print(f"✅ url_for('global_admin_events') → {url}")
        except Exception as e:
            print(f"❌ url_for('global_admin_events') → ERROR: {e}")
            all_good = False

        try:
            url = url_for('global_admin_contests')
            print(f"✅ url_for('global_admin_contests') → {url}")
        except Exception as e:
            print(f"❌ url_for('global_admin_contests') → ERROR: {e}")
            all_good = False

    print("\n" + "="*70)
    if all_good:
        print("✅ ALL ROUTES REGISTERED CORRECTLY")
    else:
        print("❌ SOME ROUTES HAVE ISSUES")
    print("="*70)

    return all_good

if __name__ == '__main__':
    success = test_all_routes()
    exit(0 if success else 1)
