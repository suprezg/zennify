"""
File Name: test_shop_service.py
Purpose: Unit tests for the Shop service layer.
"""

import pytest
from unittest.mock import patch, MagicMock
from core.shop.service import ShopMain
from core.shared.storage import StorageManager

@pytest.fixture
def mock_storage(tmp_path):
    """
    Provides a real temporary storage for testing.
    """
    db_file = tmp_path / "shop_test.db"
    storage = StorageManager(db_path=str(db_file))
    return storage

def test_shop_item_management(mock_storage):
    """
    Tests adding and removing items from the shop.
    """
    with patch("core.shop.service.StorageManager", return_value=mock_storage):
        shop = ShopMain()

        shop.add_item("Netflix session", 50)
        items = shop.get_items()
        assert len(items) == 1
        assert items[0][1] == "Netflix session"
        assert items[0][2] == 50

        item_id = items[0][0]
        shop.remove_item(item_id)
        assert len(shop.get_items()) == 0

def test_shop_purchase_logic(mock_storage):
    """
    Tests purchasing an item with sufficient and insufficient funds.
    """
    mock_wallet = MagicMock()
    
    with patch("core.shop.service.StorageManager", return_value=mock_storage), \
         patch("core.shop.service.WalletManager", return_value=mock_wallet):
        
        shop = ShopMain()
        shop.add_item("Game hour", 100)
        item_id = shop.get_items()[0][0]

        with patch.object(shop, 'give_wallet_details', return_value=(150, 0)):
            success = shop.buy_item(item_id, 100)
            assert success is True
            mock_wallet.earn_coins.assert_called_with(-100)

        with patch.object(shop, 'give_wallet_details', return_value=(50, 0)):
            success = shop.buy_item(item_id, 100)
            assert success is False

def test_shop_bankruptcy_logic():
    """
    Tests bankruptcy effect on streaks and multipliers.
    """
    mock_wallet = MagicMock()
    mock_config = MagicMock()
    
    with patch("core.shop.service.WalletManager", return_value=mock_wallet), \
         patch("core.shop.service.ConfigManager", return_value=mock_config), \
         patch("core.shop.service.StorageManager", MagicMock()):
        
        shop = ShopMain()
        shop.declare_bankrupt()

        mock_wallet.declare_bankrupt.assert_called_once()

        for feature in ["activity", "todo", "flashcard"]:
            mock_config.update_value.assert_any_call(feature, "streak", 0)
            mock_config.update_value.assert_any_call(feature, "multiplier", 1.0)
