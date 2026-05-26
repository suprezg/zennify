"""
File Name: test_activity_service.py
Purpose: Unit tests for the Activity Tracker service layers.
"""

import os
import pytest
from unittest.mock import patch, MagicMock
from core.activity.service import ActivityOverlay, ActivitySettings, ActivityStatistics, ActivityReview
from core.shared.storage import StorageManager

@pytest.fixture
def mock_storage(tmp_path):
    """
    Provides a real temporary storage for testing.
    """
    db_file = tmp_path / "activity_test.db"
    storage = StorageManager(db_path=str(db_file))
    return storage

def test_activity_overlay_write_and_read(mock_storage):
    """
    Tests writing activity entries and retrieving recent tags.
    """
    with patch("core.activity.service.StorageManager", return_value=mock_storage):
        overlay = ActivityOverlay()
        
        overlay.write_entry("2026-05-26", "10:00", "10:30", "Coding", "work", True, 5.0)
        overlay.write_entry("2026-05-26", "11:00", "11:30", "Reading", "study", True, 5.0)
        
        tags = overlay.get_recent_tags()
        assert "study" in tags
        assert "work" in tags
        
        last = overlay.get_last_entry()
        assert last[5] == "study"

def test_activity_settings_systemd_logic():
    """
    Tests configuration updates and systemd service generation (mocked).
    """
    mock_config = MagicMock()
    mock_config.read_value.side_effect = lambda f, k: {
        ("system", "project_root"): "/tmp/project",
        ("activity", "service_path"): "/tmp/service",
        ("activity", "timer_path"): "/tmp/timer",
        ("activity", "popup_interval_timer"): "30m",
        ("activity", "service_status"): True
    }.get((f, k))

    with patch("core.activity.service.ConfigManager", return_value=mock_config), \
         patch("core.activity.service.subprocess.run") as mock_run, \
         patch("builtins.open", MagicMock()):
        
        settings = ActivitySettings()
        
        settings.toggle_service(True)
        mock_run.assert_any_call(["systemctl", "--user", "enable", "--now", "zennify-activity.timer"], check=True)
        mock_config.update_value.assert_any_call("activity", "service_status", True)
        
        settings.change_popup_interval_timer("1h")
        mock_config.update_value.assert_any_call("activity", "popup_interval_timer", "1h")

def test_activity_statistics_overview(mock_storage):
    """
    Tests generation of statistics and charts (mocked base64).
    """
    with patch("core.activity.service.StorageManager", return_value=mock_storage):
        mock_storage.write(
            "INSERT INTO activity (date, start_time, end_time, description, tag, is_productive, retribution) VALUES (?, ?, ?, ?, ?, ?, ?)",
            ("2026-05-26", "10:00", "10:30", "Test", "work", 1, 5.0)
        )
        
        stats = ActivityStatistics()
        overview = stats.give_overview()
        
        assert len(overview) == 3
        assert overview[0]["title"] == "Productivity Ratio"
        assert "image_base64" in overview[0]

def test_activity_review_heatmap(mock_storage):
    """
    Tests heatmap data aggregation.
    """
    with patch("core.activity.service.StorageManager", return_value=mock_storage):
        mock_storage.write(
            "INSERT INTO activity (date, start_time, end_time, description, tag, is_productive, retribution) VALUES (?, ?, ?, ?, ?, ?, ?)",
            ("2026-05-26", "10:00", "10:30", "Test", "work", 1, 5.0)
        )
        
        review = ActivityReview()
        heatmap = review.get_heatmap("05", "2026")
        assert heatmap[26] == 1
        
        activities = review.get_activity("2026-05-26")
        assert len(activities) == 1
