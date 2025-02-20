import sqlite3
from datetime import datetime

import click
from flask import Flask, current_app, g
from flask.cli import with_appcontext


def get_db() -> sqlite3.Connection:
    """
    Get the database

    Examples:
        >>> get_db()

    Returns:
        The database
    """
    if "db" not in g:
        g.db = sqlite3.connect(
            current_app.config["DATABASE"], detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row

    return g.db


def close_db(e=None):
    """
    Close the database
    """
    db = g.pop("db", None)

    if db is not None:
        db.close()


def init_db():
    """
    Initialize the database

    Examples:
        >>> init_db()
    """
    db = get_db()

    with current_app.open_resource("schema.sql") as f:
        db.executescript(f.read().decode("utf8"))


def query_db(query, args=(), one=False):
    """
    Query the database

    Example:
        >>> # Get all aliases
        >>> query_db("SELECT * FROM aliases")
        []
        >>> # Get a single alias
        >>> query_db("SELECT * FROM aliases WHERE alias = ?", ("alias1",), one=True)
        {}
    Args:
        query (str): The query to execute
        args (tuple): The arguments to pass to the query
        one (bool): Whether to return a single row

    Returns:
        The result of the query
    """
    with current_app.app_context():
        cur = get_db().execute(query, args)
        rv = cur.fetchall()
        cur.close()
        return (rv[0] if rv else None) if one else rv


def exec_db(query, args=()) -> bool:
    """
    Execute a query on the database

    Args:
        query (str): The query to execute
        args (tuple): The arguments to pass to the query

    Returns:
        True if the query was executed successfully, False otherwise

    Raises:
        sqlite3.Error: If the query fails
    """

    try:
        with current_app.app_context():
            cur = get_db().execute(query, args)
            get_db().commit()
            cur.close()
    except sqlite3.Error as e:
        print(e)
        return False
    return True


@click.command("init-db")
@with_appcontext
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()
    click.echo("Initialized the database.")


sqlite3.register_converter("timestamp", lambda v: datetime.fromisoformat(v.decode()))


def init_app(app: Flask):
    """
    Initialize the app

    Examples:
        >>> from flask import Flask
        >>> app = Flask(__name__)
        >>> init_app(app)

    Args:
        app (Flask): The app to initialize
    """
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
