"""
File Name: test_todos_service.py
Purpose: Unit tests for the Todo service layers including deadline enforcement and task lifecycle.
"""

import pytest
import datetime
from unittest.mock import patch, MagicMock
from core.todos.service import TodoSettings, TodoStatistics, TodoTasks
from core.shared.storage import StorageManager

@pytest.fixture
def mock_storage(tmp_path):
    """
    Provides a real temporary storage for testing.
    """
    db_file = tmp_path / "todos_test.db"
    storage = StorageManager(db_path=str(db_file))
    return storage

def test_todo_settings():
    """
    Tests reading and updating todo configuration.
    """
    mock_config = MagicMock()
    mock_config.read_value.side_effect = lambda f, k: {
        ("todo", "max_tasks"): 5,
        ("todo", "streak"): 3,
        ("todo", "multiplier"): 1.2
    }.get((f, k))
    
    with patch("core.todos.service.ConfigManager", return_value=mock_config):
        settings = TodoSettings()
        config = settings.read_config()
        assert config["max_tasks"] == 5
        assert config["streak"] == 3
        
        settings.change_max_tasks(10)
        mock_config.update_value.assert_called_with("todo", "max_tasks", 10)

def test_todo_tasks_lifecycle(mock_storage):
    """
    Tests adding and completing tasks.
    """
    mock_wallet = MagicMock()
    mock_config = MagicMock()
    mock_config.read_value.return_value = 5
    
    with patch("core.todos.service.StorageManager", return_value=mock_storage), \
         patch("core.todos.service.WalletManager", return_value=mock_wallet), \
         patch("core.todos.service.ConfigManager", return_value=mock_config):
        
        tasks_service = TodoTasks()

        deadline = (datetime.datetime.now() + datetime.timedelta(days=1)).isoformat()
        success, msg = tasks_service.add_task("Finish Tests", deadline)
        assert success is True
        
        running = tasks_service.list_running_tasks()
        assert len(running) == 1
        assert running[0][1] == "Finish Tests"

        mock_config.read_value.side_effect = lambda f, k: 1.0 if k == "multiplier" else 0
        tasks_service.mark_task(running[0][0], "Completed")

        mock_wallet.earn_coins.assert_called_with(5)

        finalized = tasks_service.list_finalized_tasks("05", "2026")
        assert len(finalized) >= 1

def test_todo_deadline_enforcement(mock_storage):
    """
    Tests that past-due tasks are marked as failed on startup.
    """
    past_due = (datetime.datetime.now() - datetime.timedelta(days=1)).isoformat()
    mock_storage.write(
        "INSERT INTO todo (task_name, creation_date, deadline, status) VALUES (?, ?, ?, ?)",
        ("Overdue Task", "2026-05-25", past_due, "Running")
    )
    
    mock_wallet = MagicMock()
    mock_config = MagicMock()
    
    with patch("core.todos.service.StorageManager", return_value=mock_storage), \
         patch("core.todos.service.WalletManager", return_value=mock_wallet), \
         patch("core.todos.service.ConfigManager", return_value=mock_config):

        tasks_service = TodoTasks()

        task = mock_storage.read("SELECT status FROM todo WHERE task_name = 'Overdue Task'")[0]
        assert task[0] == "Failed"

        mock_wallet.earn_coins.assert_called_with(-2)

def test_todo_statistics(mock_storage):
    """
    Tests stats generation.
    """
    mock_config = MagicMock()
    mock_config.read_value.side_effect = lambda f, k: 0 if k == "streak" else 1.0
    
    with patch("core.todos.service.StorageManager", return_value=mock_storage), \
         patch("core.todos.service.ConfigManager", return_value=mock_config):
        
        stats = TodoStatistics()
        overview = stats.give_overview()
        
        assert "overview_data" in overview
        assert overview["streak"] == 0
