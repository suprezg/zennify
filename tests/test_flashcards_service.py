"""
File Name: test_flashcards_service.py
Purpose: Unit tests for the Flashcard service layers including folder scanning and FSRS logic.
"""

import os
import pytest
import datetime
from unittest.mock import patch, MagicMock
from core.flashcards.service import FlashcardSettings, FlashcardStatistics, FlashcardRevision
from core.shared.storage import StorageManager

@pytest.fixture
def mock_storage(tmp_path):
    """
    Provides a real temporary storage for testing.
    """
    db_file = tmp_path / "flashcards_test.db"
    storage = StorageManager(db_path=str(db_file))
    return storage

@pytest.fixture
def temp_flashcard_dir(tmp_path):
    """
    Creates a temporary directory with markdown flashcards.
    """
    deck_dir = tmp_path / "decks"
    deck_dir.mkdir()
    
    deck_file = deck_dir / "test_deck.md"
    content = """---
tags: flashcards
---

# Question 1
Answer 1

# Question 2
Answer 2
"""
    deck_file.write_text(content, encoding="utf-8")
    return str(deck_dir)

def test_flashcard_revision_scan_folder(mock_storage, temp_flashcard_dir):
    """
    Tests scanning a folder for flashcards and inserting them into the database.
    """
    mock_config = MagicMock()
    mock_config.read_value.return_value = temp_flashcard_dir
    
    with patch("core.flashcards.service.StorageManager", return_value=mock_storage), \
         patch("core.flashcards.service.ConfigManager", return_value=mock_config):
        
        revision = FlashcardRevision()
        revision.scan_folder()

        cards = mock_storage.read("SELECT * FROM flashcard")
        assert len(cards) == 2
        assert cards[0][2] == "test_deck"

def test_flashcard_revision_revise_deck(mock_storage, temp_flashcard_dir):
    """
    Tests retrieving cards due for revision.
    """
    mock_config = MagicMock()
    mock_config.read_value.return_value = temp_flashcard_dir
    
    with patch("core.flashcards.service.StorageManager", return_value=mock_storage), \
         patch("core.flashcards.service.ConfigManager", return_value=mock_config):
        
        revision = FlashcardRevision()
        revision.scan_folder()

        pending = revision.revise_deck("all")
        assert len(pending) == 2
        assert pending[0]["question"] in ["Question 1", "Question 2"]

def test_flashcard_revision_schedule_card(mock_storage):
    """
    Tests updating card stability/difficulty using FSRS logic.
    """
    with patch("core.flashcards.service.StorageManager", return_value=mock_storage):

        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        mock_storage.write(
            "INSERT INTO flashcard (card_id, deck_name, stability, difficulty, state, next_review, last_review) VALUES (?, ?, ?, ?, ?, ?, ?)",
            ("id1", "deck", 0, 0, 0, now, now)
        )
        
        revision = FlashcardRevision()
        revision.schdule_card("id1", 3)
        
        updated = mock_storage.read("SELECT stability, difficulty, state FROM flashcard WHERE card_id = 'id1'")[0]
        assert updated[0] > 0
        assert updated[1] > 0

def test_flashcard_statistics(mock_storage):
    """
    Tests statistical overview generation.
    """
    with patch("core.flashcards.service.StorageManager", return_value=mock_storage):
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        mock_storage.write(
            "INSERT INTO flashcard (card_id, deck_name, stability, difficulty, state, next_review, last_review) VALUES (?, ?, ?, ?, ?, ?, ?)",
            ("id1", "deck", 1.0, 5.0, 2, now, now)
        )
        
        stats = FlashcardStatistics()
        overview = stats.give_overview()
        
        assert "overview_data" in overview
        assert overview["revised_count"] == 1
