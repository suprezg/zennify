"""
File Name: test_core_main.py
Purpose: Unit tests for the main entry point and routing logic.
"""

import sys
import pytest
from unittest.mock import MagicMock, patch
import flet as ft
from core.main import main, show_help

@pytest.fixture
def mock_page():
    """
    Provides a mocked Flet Page object.
    """
    return MagicMock(spec=ft.Page)

def test_show_help(capsys):
    """
    Tests that show_help prints the usage guide.
    """
    show_help()
    captured = capsys.readouterr()
    assert "Zennify CLI - Usage Guide" in captured.out

@patch("sys.argv", ["main.py", "--activity"])
@patch("core.main.ActivityDashboard")
def test_main_routing_activity(mock_dashboard, mock_page):
    """
    Tests routing to the Activity Dashboard.
    """
    main(mock_page)
    mock_dashboard.assert_called_with(mock_page)
    mock_dashboard.return_value.view.assert_called_once()

@patch("sys.argv", ["main.py", "--pomodoro"])
@patch("core.main.PomodoroDashboard")
def test_main_routing_pomodoro(mock_dashboard, mock_page):
    """
    Tests routing to the Pomodoro Dashboard.
    """
    main(mock_page)
    mock_dashboard.assert_called_with(mock_page)
    mock_dashboard.return_value.view.assert_called_once()

@patch("sys.argv", ["main.py", "--flashcards"])
@patch("core.main.FlashcardDashboard")
def test_main_routing_flashcards(mock_dashboard, mock_page):
    """
    Tests routing to the Flashcard Dashboard.
    """
    main(mock_page)
    mock_dashboard.assert_called_with(mock_page)
    mock_dashboard.return_value.view.assert_called_once()

@patch("sys.argv", ["main.py", "--todos"])
@patch("core.main.TodoDashboard")
def test_main_routing_todos(mock_dashboard, mock_page):
    """
    Tests routing to the Todo Dashboard.
    """
    main(mock_page)
    mock_dashboard.assert_called_with(mock_page)
    mock_dashboard.return_value.view.assert_called_once()

@patch("sys.argv", ["main.py", "--shop"])
@patch("core.main.ShopDashboard")
def test_main_routing_shop(mock_dashboard, mock_page):
    """
    Tests routing to the Shop Dashboard.
    """
    main(mock_page)
    mock_dashboard.assert_called_with(mock_page)
    mock_dashboard.return_value.view.assert_called_once()

@patch("sys.argv", ["main.py", "--activity-popup"])
@patch("core.main.ActivityPopup")
def test_main_routing_popup(mock_popup, mock_page):
    """
    Tests routing to the Activity Popup.
    """
    main(mock_page)
    mock_popup.assert_called_with(mock_page)
    mock_popup.return_value.view.assert_called_once()
