"""
File Name: test_flashcards_dashboard.py
Purpose: UI tests for the FlashcardDashboard using Flet mocking.
"""

import pytest
from unittest.mock import MagicMock, patch
import flet as ft
from core.flashcards.dashboard import FlashcardDashboard

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

@patch("core.flashcards.dashboard.FlashcardRevision")
@patch("core.flashcards.dashboard.FlashcardSettings")
@patch("core.flashcards.dashboard.FlashcardStatistics")
def test_flashcards_dashboard_view(mock_stats, mock_settings, mock_revision, mock_page):
    """
    Tests if the dashboard initializes and adds tabs to the page.
    """
    mock_revision.return_value.get_deck_stats.return_value = ({"Deck1": 5}, 5)
    mock_stats.return_value.give_overview.return_value = {"overview_data": []}
    mock_settings.return_value.get_folder_path.return_value = "/tmp/flashcards"
    
    dashboard = FlashcardDashboard(mock_page)
    dashboard.view()
    
    assert mock_page.title == "Zennify - Flashcards"
    assert len(mock_page.controls) > 0
    assert isinstance(mock_page.controls[0], ft.Tabs)
    mock_page.clean.assert_called_once()

@patch("core.flashcards.dashboard.FlashcardRevision")
@patch("core.flashcards.dashboard.FlashcardSettings")
@patch("core.flashcards.dashboard.FlashcardStatistics")
def test_flashcards_dashboard_start_session(mock_stats, mock_settings, mock_revision, mock_page):
    """
    Tests starting a revision session.
    """
    mock_revision.return_value.get_deck_stats.return_value = ({"Deck1": 1}, 1)
    mock_revision.return_value.revise_deck.return_value = [
        {"id": "1", "question": "Q1", "answer": "A1", "deck": "Deck1"}
    ]
    
    dashboard = FlashcardDashboard(mock_page)
    dashboard.view()

    revision_tab = dashboard._revision_tab()

    controls = revision_tab.controls
    buttons_row = controls[-1].content.controls[-1]
    revise_btn = buttons_row.controls[-1]
    
    revise_btn.on_click(MagicMock())

    mock_page.show_dialog.assert_called_once()
    dialog = mock_page.show_dialog.call_args[0][0]
    assert "Revision Session" in dialog.title.controls[0].value
