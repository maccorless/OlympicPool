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


def load_countries():
    """Load countries from data/countries.sql if table is empty."""
    import os
    db = get_db()

    # Check if countries already loaded
    count = db.execute('SELECT COUNT(*) as count FROM countries').fetchone()['count']
    if count > 0:
        click.echo(f'Countries already loaded ({count} countries).')
        return

    # countries.sql is at project root/data
    countries_path = os.path.join(os.path.dirname(current_app.root_path), 'data', 'countries.sql')

    try:
        with open(countries_path, 'r') as f:
            countries_sql = f.read()
    except FileNotFoundError:
        logger.error(f"Countries file not found at {countries_path}")
        click.echo(f"Error: Could not find countries.sql at {countries_path}", err=True)
        raise
    except Exception as e:
        logger.error(f"Failed to read countries file: {e}")
        click.echo(f"Error: Failed to read countries.sql: {e}", err=True)
        raise

    try:
        db.executescript(countries_sql)
        db.commit()
        new_count = db.execute('SELECT COUNT(*) as count FROM countries').fetchone()['count']
        click.echo(f'Loaded {new_count} countries successfully.')
    except sqlite3.Error as e:
        logger.error(f"Failed to load countries: {e}")
        click.echo(f"Error: Failed to load countries: {e}", err=True)
        raise


@click.command('init-db')
def init_db_command():
    """CLI command to initialize the database."""
    init_db()
    click.echo('Initialized the database.')


@click.command('load-countries')
def load_countries_command():
    """CLI command to load countries data."""
    load_countries()


def init_app(app):
    """Register database functions with Flask app."""
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
    app.cli.add_command(load_countries_command)
