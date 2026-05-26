"""
File Name: test_shop_dashboard.py
Purpose: UI tests for the ShopDashboard using Flet mocking.
"""

import pytest
from unittest.mock import MagicMock, patch
import flet as ft
from core.shop.dashboard import ShopDashboard

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

@patch("core.shop.dashboard.ShopMain")
@patch("core.shop.dashboard.WalletManager")
def test_shop_dashboard_view(mock_wallet, mock_shop, mock_page):
    """
    Tests if the shop dashboard initializes and renders correctly.
    """
    mock_shop.return_value.give_wallet_details.return_value = (100, 0)
    mock_shop.return_value.get_items.return_value = [
        (1, "Test Item", 50, 2)
    ]
    mock_wallet.return_value.is_bankrupt.return_value = 1
    
    dashboard = ShopDashboard(mock_page)
    dashboard.view()
    
    assert mock_page.title == "Zennify - Reward Shop"
    assert len(mock_page.controls) > 0

    main_container = mock_page.controls[0]
    column = main_container.content

    header = column.controls[0]
    assert "Coins: 100" in header.content.controls[0].controls[1].value

    inventory_container = column.controls[2]

    inventory_view = inventory_container.content.controls[2].content
    assert len(inventory_view.controls) == 1
    assert "Test Item" in inventory_view.controls[0].content.content.controls[0].title.value

@patch("core.shop.dashboard.ShopMain")
@patch("core.shop.dashboard.WalletManager")
def test_shop_dashboard_toggle_view(mock_wallet, mock_shop, mock_page):
    """
    Tests toggling between grid and list views.
    """
    mock_shop.return_value.give_wallet_details.return_value = (100, 0)
    mock_shop.return_value.get_items.return_value = []
    
    dashboard = ShopDashboard(mock_page)
    dashboard.view()
    
    assert dashboard.view_mode == "grid"
    
    column = mock_page.controls[0].content
    inventory_container = column.controls[2]
    toggle_btn = inventory_container.content.controls[0].controls[1]

    toggle_btn.on_click(MagicMock())
    
    assert dashboard.view_mode == "list"

@patch("core.shop.dashboard.ShopMain")
@patch("core.shop.dashboard.WalletManager")
def test_shop_dashboard_buy_item_dialog(mock_wallet, mock_shop, mock_page):
    """
    Tests that clicking 'Buy' opens a confirmation dialog.
    """
    mock_shop.return_value.give_wallet_details.return_value = (100, 0)
    mock_shop.return_value.get_items.return_value = [(1, "Test Item", 50, 0)]
    
    dashboard = ShopDashboard(mock_page)
    dashboard.view()

    column = mock_page.controls[0].content
    inventory_view = column.controls[2].content.controls[2].content
    item_card = inventory_view.controls[0]
    buy_btn = item_card.content.content.controls[1].controls[0]

    buy_btn.on_click(MagicMock())

    mock_page.show_dialog.assert_called_once()
    dialog = mock_page.show_dialog.call_args[0][0]
    assert "Confirm Purchase" in dialog.title.value
