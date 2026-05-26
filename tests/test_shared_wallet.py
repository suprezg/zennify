"""
File Name: test_shared_wallet.py
Purpose: Unit tests for the WalletManager class.
"""

import pytest
from unittest.mock import patch, MagicMock
from core.shared.wallet import WalletManager
from core.shared.storage import StorageManager

@pytest.fixture
def mock_storage(tmp_path):
    """
    Provides a WalletManager with a real temporary storage for testing.
    """
    db_file = tmp_path / "wallet_test.db"
    storage = StorageManager(db_path=str(db_file))
    
    with patch("core.shared.wallet.StorageManager", return_value=storage):
        manager = WalletManager()
        yield manager, storage
    
    storage.close()

def test_wallet_earn_coins(mock_storage):
    """
    Tests earning and losing coins, including the debt limit.
    """
    manager, storage = mock_storage

    assert manager.is_bankrupt() == 1

    manager.earn_coins(50)
    assert storage.read("SELECT total_coins FROM wallet WHERE id = 1")[0][0] == 50

    manager.earn_coins(-20)
    assert storage.read("SELECT total_coins FROM wallet WHERE id = 1")[0][0] == 30

    manager.earn_coins(-200)
    assert storage.read("SELECT total_coins FROM wallet WHERE id = 1")[0][0] == -75
    assert manager.is_bankrupt() == -1

def test_wallet_declare_bankrupt(mock_storage):
    """
    Tests the bankruptcy declaration process.
    """
    manager, storage = mock_storage

    manager.earn_coins(-50)
    assert manager.is_bankrupt() == -1

    with patch("builtins.input", return_value="yes"):
        manager.declare_bankrupt()

    records = storage.read("SELECT total_coins, bankruptcy_count FROM wallet WHERE id = 1")[0]
    assert records[0] == 0
    assert records[1] == 1
    assert manager.is_bankrupt() == 1

def test_wallet_declare_bankrupt_cancel(mock_storage):
    """
    Tests cancelling the bankruptcy declaration.
    """
    manager, storage = mock_storage

    manager.earn_coins(-50)

    with patch("builtins.input", return_value="no"):
        manager.declare_bankrupt()

    records = storage.read("SELECT total_coins, bankruptcy_count FROM wallet WHERE id = 1")[0]
    assert records[0] == -50
    assert records[1] == 0
