"""
File Name: storage.py
Purpose: Handle all SQLite database creation, reading, and writing for the Zennify ecosystem.
"""

import sqlite3
import os
import json
from core.shared.configurator import ConfigManager

class StorageManager:
    """
    Manages the SQLite database connection and operations for the application.
    This class handles initialization, schema creation, and generic read/write operations.
    """

    def __init__(self, db_path=None):
        """
        Initializes the database connection and prepares tables.

        Takes:
            db_path (str, optional): The absolute path to the SQLite database file.
                If None, the path is retrieved from the configuration manager.

        Gives:
            None: Initializes the instance attributes 'conn' and 'cursor'.
        """
        if db_path is None:
            self.db_path = ConfigManager().read_value("system","database_path")
        else:
            self.db_path = db_path

        db_exists = os.path.exists(self.db_path)
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()

        if not db_exists:
            self._initialize_tables()

    def _initialize_tables(self):
        """
        Creates the database schema and default records if they do not exist.

        Takes:
            None: Operates on the internal database connection.

        Gives:
            None: Executes the SQL schema and commits changes to the database.
        """
        schema = """
        CREATE TABLE IF NOT EXISTS activity (
            session_id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            start_time TEXT,
            end_time TEXT,
            description TEXT,
            tag TEXT,
            is_productive BOOLEAN,
            retribution REAL
        );
        CREATE TABLE IF NOT EXISTS flashcard (
            card_id TEXT PRIMARY KEY,
            content_hash TEXT,
            deck_name TEXT,
            stability REAL,
            difficulty REAL,
            state INTEGER,
            next_review TEXT,
            last_review TEXT
        );
        CREATE TABLE IF NOT EXISTS todo (
            task_id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_name TEXT,
            creation_date TEXT,
            deadline TEXT,
            status TEXT,
            completion_time TEXT,
            retribution REAL
        );
        CREATE TABLE IF NOT EXISTS pomodoro (
            session_id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            start_time TEXT,
            end_time TEXT,
            duration_mins INTEGER,
            phase TEXT
        );
        CREATE TABLE IF NOT EXISTS shop (
            item_id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT,
            cost INTEGER,
            purchase_count INTEGER
        );
        CREATE TABLE IF NOT EXISTS wallet (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            total_coins REAL DEFAULT 0,
            bankruptcy_count INTEGER DEFAULT 0
        );
        INSERT OR IGNORE INTO wallet (id, total_coins, bankruptcy_count) VALUES (1, 0, 0);
        """
        self.cursor.executescript(schema)
        self.conn.commit()

    def read(self, query, params=()):
        """
        Executes a database query to retrieve data.

        Takes:
            query (str): The SQL SELECT statement to execute.
            params (tuple, optional): Parameters to bind to the query for safety.

        Gives:
            list: A list of tuples containing the result rows from the database.
        """
        self.cursor.execute(query, params)
        return self.cursor.fetchall()

    def write(self, query, params=()):
        """
        Executes a database query to modify data.

        Takes:
            query (str): The SQL statement (INSERT, UPDATE, DELETE) to execute.
            params (tuple, optional): Parameters to bind to the query for safety.

        Gives:
            None: Commits the changes resulting from the query to the database.
        """
        self.cursor.execute(query, params)
        self.conn.commit()

    def close(self):
        """
        Closes the active database connection and cursor.

        Takes:
            None: Operates on the internal connection objects.

        Gives:
            None: Ensures the database connection is properly terminated.
        """
        self.conn.close()
