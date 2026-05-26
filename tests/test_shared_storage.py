"""
File Name: test_shared_storage.py
Purpose: Unit tests for the StorageManager class.
"""

import os
import sqlite3
import pytest
from core.shared.storage import StorageManager

@pytest.fixture
def temp_db(tmp_path):
    """
    Creates a temporary database path for testing.
    """
    db_file = tmp_path / "test_zennify.db"
    return str(db_file)

def test_storage_manager_initialization(temp_db):
    """
    Tests if the StorageManager correctly initializes the database and tables.
    """
    storage = StorageManager(db_path=temp_db)

    assert os.path.exists(temp_db)

    tables = storage.read("SELECT name FROM sqlite_master WHERE type='table'")
    table_names = [t[0] for t in tables]
    assert "activity" in table_names
    assert "flashcard" in table_names
    assert "todo" in table_names
    assert "pomodoro" in table_names
    assert "shop" in table_names
    assert "wallet" in table_names

    wallet = storage.read("SELECT * FROM wallet")
    assert len(wallet) == 1
    assert wallet[0][0] == 1
    assert wallet[0][1] == 0
    
    storage.close()

def test_storage_manager_write_read(temp_db):
    """
    Tests writing to and reading from the database.
    """
    storage = StorageManager(db_path=temp_db)

    storage.write(
        "INSERT INTO activity (date, description, tag, is_productive, retribution) VALUES (?, ?, ?, ?, ?)",
        ("2026-05-26", "Test activity", "test", 1, 5.0)
    )

    rows = storage.read("SELECT description, retribution FROM activity WHERE tag = ?", ("test",))
    assert len(rows) == 1
    assert rows[0][0] == "Test activity"
    assert rows[0][1] == 5.0
    
    storage.close()

def test_storage_manager_update(temp_db):
    """
    Tests updating records in the database.
    """
    storage = StorageManager(db_path=temp_db)

    storage.write("UPDATE wallet SET total_coins = ? WHERE id = 1", (100.0,))

    wallet = storage.read("SELECT total_coins FROM wallet WHERE id = 1")
    assert wallet[0][0] == 100.0
    
    storage.close()
