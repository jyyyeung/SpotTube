"""
Configure aliases for artists
"""

import pathlib
from dataclasses import dataclass, field

import yaml
from flask import current_app

from src.db import exec_db, query_db


@dataclass
class Aliases:
    """
    Aliases for artists
    """

    _aliases: dict[str, str] = field(default_factory=dict)

    def __init__(self):
        self._aliases = {}
        with current_app.app_context():
            self.refresh()

    def refresh(self):
        """
        Refresh the aliases by loading them from the database
        """
        self.load_from_db()

    @property
    def aliases(self) -> dict[str, str]:
        """
        Get the aliases
        """
        # Don't refresh on every get, as it requires db access
        return self._aliases

    @aliases.setter
    def aliases(self, value: dict[str, str]):
        """
        Set the aliases
        """
        self._aliases = value
        # Update the database
        # self._save_aliases(value)

    def import_from_file(self, file_path: pathlib.Path):
        """
        Import aliases from a file

        Examples:
            >>> Aliases().import_from_file(pathlib.Path("aliases.yaml"))

        Args:
            file_path (pathlib.Path): The path to the file containing the aliases
        """
        with open(file_path, "r", encoding="utf-8") as f:
            try:
                aliases = yaml.safe_load(f)
                print(aliases)
                self._save_aliases(aliases)
            except yaml.YAMLError as exc:
                print(exc)

    def _save_aliases(self, file_aliases: dict[str, list[str]]):
        """
        Save the aliases to the database

        Examples:
            >>> _save_aliases({"artist1": ["alias1", "alias2"], "artist2": ["alias3"]})

        Args:
            file_aliases (dict[str, list[str]]): The aliases to save
        """
        for artist, artist_aliases in file_aliases.items():
            for alias in artist_aliases:
                exec_db(
                    "INSERT OR REPLACE INTO aliases (alias, artist) VALUES (?, ?)",
                    (alias, artist),
                )

    def load_from_db(self) -> bool:
        """
        Load aliases from the database

        Examples:
            >>> Aliases().load_from_db()

        Returns:
            bool: True if the aliases were loaded, False otherwise
        """
        # Only if the aliases table exists
        res = query_db(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='aliases'"
        )
        if res is None:
            return False

        res = query_db("SELECT alias, artist FROM aliases")
        self.aliases = dict(res)
        return True

    def get_name(self, alias: str) -> str:
        """
        Get the artist for an alias

        Examples:
            >>> Aliases().get_name("alias1")

        Args:
            alias (str): The alias to get the artist for

        Returns:
            str: The artist for the alias (if it exists) or the alias itself
        """
        return self._aliases.get(alias, alias)

    def add_aliases(self, aliases: dict[str, str]):
        """
        Batch add aliases for artists

        Examples:
            >>> aliases = Aliases()
            >>> aliases.add_aliases({"alias1": "artist1", "alias2": "artist2"})

        Args:
            aliases (dict[str, str]): The aliases to add

        Raises:
            sqlite3.Error: If the query fails
        """
        for alias, artist in aliases.items():
            self._aliases[alias] = artist
            exec_db(
                "INSERT INTO aliases (alias, artist) VALUES (?, ?)", (alias, artist)
            )
        self.refresh()

    def add_alias(self, alias: str, artist: str):
        """
        Add an alias for an artist

        Examples:
            >>> aliases = Aliases()
            >>> aliases.add_alias("alias1", "artist1")

        Args:
            alias (str): The alias to add
            artist (str): The artist to add the alias to
        """
        exec_db("INSERT INTO aliases (alias, artist) VALUES (?, ?)", (alias, artist))
        self._aliases[alias] = artist
        self.refresh()

    def remove_alias(self, alias: str):
        """
        Remove an alias for an artist

        Examples:
            >>> aliases = Aliases()
            >>> aliases.remove_alias("alias1")

        Args:
            alias (str): The alias to remove
        """
        self.aliases.pop(alias)
        exec_db("DELETE FROM aliases WHERE alias = ?", (alias,))
        self.refresh()
