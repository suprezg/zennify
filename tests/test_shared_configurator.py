"""
File Name: test_shared_configurator.py
Purpose: Unit tests for the ConfigManager class.
"""

import json
import os
import pytest
from unittest.mock import patch
from core.shared.configurator import ConfigManager

@pytest.fixture
def temp_config_file(tmp_path):
    """
    Creates a temporary config file for testing.
    """
    config_data = {
        "activity_config": {
            "streak": 5,
            "multiplier": 1.5
        },
        "pomodoro_config": {
            "work_time": "60m"
        }
    }
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps(config_data, indent=4))
    return str(config_file)

def test_config_manager_read_value(temp_config_file):
    """
    Tests reading values from the configuration file.
    """
    with patch.dict(os.environ, {"ZENNIFY_CONFIG_PATH": temp_config_file}):
        manager = ConfigManager()

        assert manager.read_value("activity", "streak") == 5
        assert manager.read_value("pomodoro", "work_time") == "60m"

        assert manager.read_value("activity", "non_existent") is None
        assert manager.read_value("non_existent_feature", "key") is None

def test_config_manager_update_value(temp_config_file):
    """
    Tests updating values in the configuration file.
    """
    with patch.dict(os.environ, {"ZENNIFY_CONFIG_PATH": temp_config_file}):
        manager = ConfigManager()

        manager.update_value("activity", "streak", 10)
        assert manager.read_value("activity", "streak") == 10

        manager.update_value("todo", "max_tasks", 5)
        assert manager.read_value("todo", "max_tasks") == 5

        with open(temp_config_file, "r") as f:
            data = json.load(f)
            assert data["todo_config"]["max_tasks"] == 5
