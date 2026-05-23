"""
File Name: storage.py
Purpose: Handle all SQLite database creation, reading, and writing for the Zennify ecosystem.
"""

import sqlite3
import os
import json


class StorageManager:
    """
    Manages the SQLite database connection and operations.
    """

    def __init__(self, db_path=None):
        """
        Initializes the database connection and tables.
        If db_path is not provided, it reads from config.json.
        """
        if db_path is None:
            self.db_path = self._get_db_path_from_config()
        else:
            self.db_path = db_path

        db_exists = os.path.exists(self.db_path)
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()

        if not db_exists:
            self._initialize_tables()

    def _get_db_path_from_config(self):
        """
        Reads the database path from config.json.

        Takes: None
        Gives: str (path to database)
        """
        config_path = os.getenv("ZENNIFY_CONFIG_PATH")
        if not config_path:
            config_path = os.path.join(os.getcwd(), "config.json")
            
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                config = json.load(f)
                return config.get("system_config", {}).get("database_path", "zennify_storage.db")
        return "zennify_storage.db"

    def _initialize_tables(self):
        """
        Creates the necessary tables if they do not exist.
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
            retribution REAL
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
        Executes a SELECT query and returns all results.
        """
        self.cursor.execute(query, params)
        return self.cursor.fetchall()

    def write(self, query, params=()):
        """
        Executes a DML query (INSERT, UPDATE, DELETE) and commits.
        """
        self.cursor.execute(query, params)
        self.conn.commit()

    def close(self):
        """
        Closes the database connection.
        """
        self.conn.close()
