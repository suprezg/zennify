"""
File Name: test_activity_dashboard.py
Purpose: UI tests for the ActivityDashboard using Flet mocking.
"""

import pytest
from unittest.mock import MagicMock, patch
import flet as ft
from core.activity.dashboard import ActivityDashboard

@pytest.fixture
def mock_page():
    """
    Provides a mocked Flet Page object.
    """
    page = MagicMock(spec=ft.Page)
    page.window = MagicMock()
    page.controls = []
    
    def mock_add(*args):
        page.controls.extend(args)
    page.add.side_effect = mock_add
    
    return page

@patch("core.activity.dashboard.ActivitySettings")
@patch("core.activity.dashboard.ActivityStatistics")
@patch("core.activity.dashboard.ActivityReview")
@patch("core.activity.dashboard.WalletManager")
def test_activity_dashboard_view(mock_wallet, mock_review, mock_stats, mock_settings, mock_page):
    """
    Tests if the dashboard initializes correctly and adds tabs to the page.
    """
    mock_settings.return_value.get_streak_data.return_value = (5, 1.5)
    mock_stats.return_value.give_overview.return_value = []
    mock_settings.return_value.get_service_details.return_value = ["path", "timer", True]
    mock_settings.return_value.get_timer_details.return_value = ["30m", "2m"]
    mock_wallet.return_value.is_bankrupt.return_value = 1
    
    dashboard = ActivityDashboard(mock_page)
    dashboard.view()
    
    assert mock_page.title == "Zennify - Activity Tracker"
    assert mock_page.theme_mode == ft.ThemeMode.DARK
    
    assert len(mock_page.controls) > 0
    assert isinstance(mock_page.controls[0], ft.Tabs)
    
    mock_page.clean.assert_called_once()

@patch("core.activity.dashboard.ActivitySettings")
@patch("core.activity.dashboard.ActivityStatistics")
@patch("core.activity.dashboard.ActivityReview")
@patch("core.activity.dashboard.WalletManager")
def test_activity_dashboard_wallet_warning(mock_wallet, mock_review, mock_stats, mock_settings, mock_page):
    """
    Tests if the wallet warning dialog is shown when bankrupt.
    """
    mock_wallet.return_value.is_bankrupt.return_value = -1
    mock_settings.return_value.get_streak_data.return_value = (0, 1.0)
    mock_stats.return_value.give_overview.return_value = []
    mock_settings.return_value.get_service_details.return_value = ["path", "timer", False]
    mock_settings.return_value.get_timer_details.return_value = ["30m", "2m"]
    
    dashboard = ActivityDashboard(mock_page)
    dashboard.view()
    
    mock_page.show_dialog.assert_called_once()
    dialog = mock_page.show_dialog.call_args[0][0]
    assert "Wallet Warning" in dialog.title.value
