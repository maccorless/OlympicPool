"""
Database connection and helpers using sqlite3.
"""
import sqlite3
import logging
import click
from flask import current_app, g

logger = logging.getLogger(__name__)


def get_db():
    """Get database connection for current request."""
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row
        # Enable foreign key constraints (required per connection)
        g.db.execute('PRAGMA foreign_keys = ON')
    return g.db


def close_db(e=None):
    """Close database connection at end of request."""
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db():
    """Initialize database with schema."""
    import os
    db = get_db()

    # schema.sql is at project root (one level up from app/)
    schema_path = os.path.join(os.path.dirname(current_app.root_path), 'schema.sql')

    try:
        with open(schema_path, 'r') as f:
            schema_sql = f.read()
    except FileNotFoundError:
        logger.error(f"Schema file not found at {schema_path}")
        click.echo(f"Error: Could not find schema.sql at {schema_path}", err=True)
        raise
    except Exception as e:
        logger.error(f"Failed to read schema file: {e}")
        click.echo(f"Error: Failed to read schema.sql: {e}", err=True)
        raise

    try:
        db.executescript(schema_sql)
        db.commit()
    except sqlite3.Error as e:
        logger.error(f"Failed to execute schema: {e}")
        click.echo(f"Error: Failed to initialize database: {e}", err=True)
        raise

    # Enable WAL mode (persistent setting, only needed once)
    db.execute('PRAGMA journal_mode = WAL')


@click.command('init-db')
def init_db_command():
    """CLI command to initialize the database."""
    init_db()
    click.echo('Initialized the database.')


def init_app(app):
    """Register database functions with Flask app."""
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
