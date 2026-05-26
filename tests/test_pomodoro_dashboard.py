"""
File Name: test_pomodoro_dashboard.py
Purpose: UI tests for the PomodoroDashboard using Flet mocking.
"""

import pytest
from unittest.mock import MagicMock, patch
import flet as ft
from core.pomodoro.dashboard import PomodoroDashboard

@pytest.fixture
def mock_page():
    """
    Provides a mocked Flet Page object.
    """
    page = MagicMock(spec=ft.Page)
    page.window = MagicMock()
    page.controls = []
    page.add.side_effect = lambda *args: page.controls.extend(args)
    page.overlay = []
    return page

@patch("core.pomodoro.dashboard.PomodoroTimer")
@patch("core.pomodoro.dashboard.PomodoroSettings")
@patch("core.pomodoro.dashboard.PomodoroStatistics")
def test_pomodoro_dashboard_view(mock_stats, mock_settings, mock_timer, mock_page):
    """
    Tests if the dashboard initializes and adds tabs to the page.
    """
    mock_settings.return_value.get_preset.return_value = {
        "work_time": "60m", "short_break_time": "5m", "long_break_time": "15m", "long_break_interval": 4
    }
    mock_timer.return_value.get_current_state.return_value = {
        "phase": "Work", "is_running": False, "remaining_seconds": 3600
    }
    mock_stats.return_value.give_overview.return_value = []
    
    dashboard = PomodoroDashboard(mock_page)
    dashboard.view()
    
    assert mock_page.title == "Zennify - Pomodoro Timer"
    assert len(mock_page.controls) > 0
    assert isinstance(mock_page.controls[0], ft.Tabs)
    mock_page.clean.assert_called_once()

@patch("core.pomodoro.dashboard.PomodoroTimer")
@patch("core.pomodoro.dashboard.PomodoroSettings")
@patch("core.pomodoro.dashboard.PomodoroStatistics")
def test_pomodoro_dashboard_timer_start(mock_stats, mock_settings, mock_timer, mock_page):
    """
    Tests starting the timer from the dashboard.
    """
    mock_settings.return_value.get_preset.return_value = {
        "work_time": "60m", "short_break_time": "5m", "long_break_time": "15m", "long_break_interval": 4
    }
    mock_timer.return_value.get_current_state.return_value = {
        "phase": "Work", "is_running": False, "remaining_seconds": 3600
    }
    
    dashboard = PomodoroDashboard(mock_page)
    timer_tab = dashboard._timer_tab()

    buttons_row = timer_tab.controls[5]
    start_btn = buttons_row.controls[0]
    
    start_btn.on_click(MagicMock())

    mock_timer.return_value.start.assert_called_once()
    mock_page.run_task.assert_called()
