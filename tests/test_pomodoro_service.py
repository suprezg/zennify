"""
File Name: test_pomodoro_service.py
Purpose: Unit tests for the Pomodoro service layers including timer logic and state persistence.
"""

import os
import json
import pytest
import time
from unittest.mock import patch, MagicMock
from core.pomodoro.service import PomodoroSettings, PomodoroStatistics, PomodoroTimer
from core.shared.storage import StorageManager

@pytest.fixture
def mock_config():
    """
    Mocked ConfigManager for Pomodoro settings.
    """
    mock = MagicMock()
    mock.read_value.side_effect = lambda f, k: {
        ("pomodoro", "work_time"): "60m",
        ("pomodoro", "short_break_time"): "5m",
        ("pomodoro", "long_break_time"): "15m",
        ("pomodoro", "long_break_interval"): 4
    }.get((f, k))
    mock.config_path = "/tmp/config.json"
    return mock

@pytest.fixture
def temp_state_file(tmp_path):
    """
    Temporary state file for timer persistence.
    """
    return str(tmp_path / "pomodoro_state.json")

def test_pomodoro_settings(mock_config):
    """
    Tests reading and changing pomodoro presets.
    """
    with patch("core.pomodoro.service.ConfigManager", return_value=mock_config):
        settings = PomodoroSettings()
        presets = settings.get_preset()
        assert presets["work_time"] == "60m"
        
        settings.change_preset("30m", "5m", "15m", 2)
        mock_config.update_value.assert_called()

def test_pomodoro_timer_logic(mock_config, temp_state_file):
    """
    Tests the timer lifecycle and phase transitions.
    """
    with patch("core.pomodoro.service.ConfigManager", return_value=mock_config), \
         patch("core.pomodoro.service.os.path.join", return_value=temp_state_file):
        
        timer = PomodoroTimer()
        assert timer.state["phase"] == "Work"
        assert timer.state["remaining_seconds"] == 3600

        timer.start()
        assert timer.state["is_running"] is True
        assert timer.state["last_update"] is not None

        timer.pause()
        assert timer.state["is_running"] is False
        assert timer.state["last_update"] is None

        timer.change_phase()
        assert timer.state["phase"] == "Short Break"
        assert timer.state["remaining_seconds"] == 300
        assert timer.state["completed_pomodoros"] == 1

        timer.restart()
        assert timer.state["phase"] == "Work"
        assert timer.state["completed_pomodoros"] == 0

def test_pomodoro_timer_long_break(mock_config, temp_state_file):
    """
    Tests transitioning to a long break after the configured interval.
    """
    with patch("core.pomodoro.service.ConfigManager", return_value=mock_config), \
         patch("core.pomodoro.service.os.path.join", return_value=temp_state_file):
        
        timer = PomodoroTimer()
        timer.state["completed_pomodoros"] = 3

        timer.change_phase()
        assert timer.state["phase"] == "Long Break"
        assert timer.state["remaining_seconds"] == 900

def test_pomodoro_statistics(tmp_path):
    """
    Tests generation of statistics.
    """
    db_file = tmp_path / "pomodoro_test.db"
    storage = StorageManager(db_path=str(db_file))
    
    with patch("core.pomodoro.service.StorageManager", return_value=storage):
        storage.write(
            "INSERT INTO pomodoro (date, start_time, end_time, duration_mins, phase) VALUES (?, ?, ?, ?, ?)",
            ("2026-05-26", "10:00", "11:00", 60, "Work")
        )
        
        stats = PomodoroStatistics()
        overview = stats.give_overview()
        
        assert len(overview) > 0
        assert overview[0]["title"] == "Total Zen Time"
        assert "1h" in overview[0]["value"]
    
    storage.close()
