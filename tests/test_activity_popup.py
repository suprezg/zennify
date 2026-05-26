"""
File Name: test_activity_popup.py
Purpose: UI tests for the ActivityPopup using Flet mocking.
"""

import pytest
import datetime
from unittest.mock import MagicMock, patch
import flet as ft
from core.activity.popup import ActivityPopup

@pytest.fixture
def mock_page():
    """
    Provides a mocked Flet Page object.
    """
    page = MagicMock(spec=ft.Page)
    page.window = MagicMock()
    page.controls = []
    page.add.side_effect = lambda *args: page.controls.extend(args)
    return page

@patch("core.activity.popup.ActivitySettings")
@patch("core.activity.popup.ActivityOverlay")
@patch("core.activity.popup.WalletManager")
def test_activity_popup_view(mock_wallet, mock_overlay, mock_settings, mock_page):
    """
    Tests if the popup initializes and renders controls.
    """
    mock_settings.return_value.get_timer_details.return_value = ("30m", "2m")
    mock_overlay.return_value.get_recent_tags.return_value = ["tag1", "tag2"]
    
    popup = ActivityPopup(mock_page)
    popup.view()
    
    assert mock_page.title == "Zennify - Log Activity"
    assert len(mock_page.controls) > 0
    assert isinstance(mock_page.controls[0], ft.Container)
    mock_page.run_task.assert_called()

@patch("core.activity.popup.ActivitySettings")
@patch("core.activity.popup.ActivityOverlay")
@patch("core.activity.popup.WalletManager")
def test_activity_popup_submit_manual(mock_wallet, mock_overlay, mock_settings, mock_page):
    """
    Tests manual submission of activity logs.
    """
    mock_settings.return_value.get_timer_details.return_value = ("30m", "2m")
    mock_settings.return_value.get_streak_data.return_value = (5, 1.5)
    mock_overlay.return_value.get_last_entry.return_value = [0,0,0,0,0,0, True]
    
    popup = ActivityPopup(mock_page)
    popup.description_input.value = "Test task"
    popup.tag_dropdown.value = "work"
    popup.productivity_radio.value = "productive"
    
    popup._submit(auto=False)
    
    mock_settings.return_value.update_streak_data.assert_called_with(6, 1.6)
    mock_wallet.return_value.earn_coins.assert_called_with(8)
    mock_overlay.return_value.write_entry.assert_called()
    mock_page.run_task.assert_any_call(mock_page.window.destroy)

@patch("core.activity.popup.ActivitySettings")
@patch("core.activity.popup.ActivityOverlay")
@patch("core.activity.popup.WalletManager")
def test_activity_popup_submit_auto(mock_wallet, mock_overlay, mock_settings, mock_page):
    """
    Tests automatic submission (timeout) of activity logs.
    """
    mock_settings.return_value.get_timer_details.return_value = ("30m", "2m")
    mock_settings.return_value.get_streak_data.return_value = (5, 1.5)
    
    popup = ActivityPopup(mock_page)
    popup._submit(auto=True)
    
    mock_settings.return_value.update_streak_data.assert_called_with(0, 1.0)
    mock_wallet.return_value.earn_coins.assert_called_with(-2)
    mock_overlay.return_value.write_entry.assert_called_with(
        pytest.any, pytest.any, pytest.any, "Inactive", "Inactive", False, -2
    )
