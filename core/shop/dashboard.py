"""
File Name: dashboard.py
Purpose: User interface for the Shop feature.
"""

import flet as ft
from core.shop.service import ShopMain
from core.shared.wallet import WalletManager


class ShopDashboard:
    """
    Main dashboard class for the Shop feature.
    """

    def __init__(self, page):
        """
        Initializes the dashboard with the Flet page.

        Takes:
          page (ft.Page): The Flet page instance.

        Gives:
          None.
        """
        self.page = page
        self.shop_service = ShopMain()
        self.view_mode = "grid"
    def view(self):
        """
        Builds and displays the main view for the shop.

        Takes:
          None.

        Gives:
          None.
        """
        self.page.title = "Zennify - Reward Shop"
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.window.min_width = 800
        self.page.window.min_height = 600
        self.page.clean()


        wallet_details = self.shop_service.give_wallet_details()
        coins, bankruptcies = wallet_details
        items = self.shop_service.get_items()

        header = ft.Container(
            content=ft.Row([
                ft.Row([
                    ft.Icon(ft.Icons.MONETIZATION_ON, color=ft.Colors.AMBER, size=30),
                    ft.Text(f"Coins: {coins}", size=24, weight=ft.FontWeight.BOLD)
                ], spacing=10),
                ft.Row([
                    ft.Icon(ft.Icons.DANGEROUS, color=ft.Colors.RED_400, size=30),
                    ft.Text(f"Bankruptcies: {bankruptcies}", size=24, weight=ft.FontWeight.BOLD)
                ], spacing=10)
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=100),
            padding=30
        )

        item_name_input = ft.TextField(label="Reward Name", expand=True, hint_text="e.g., Watch a movie")
        item_cost_dropdown = ft.Dropdown(
            label="Cost",
            options=[ft.dropdown.Option("50"), ft.dropdown.Option("75"), ft.dropdown.Option("100")],
            value="50",
            width=100
        )

        def add_item(e):
            """
            Adds a new custom item to the shop.

            Takes:
              e (ft.ControlEvent): The event object.

            Gives:
              None.
            """
            if item_name_input.value:
                self.shop_service.add_item(item_name_input.value, int(item_cost_dropdown.value))
                self.view()

        add_btn = ft.IconButton(icon=ft.Icons.ADD_CIRCLE, on_click=add_item, icon_color=ft.Colors.GREEN_ACCENT, icon_size=35)

        create_section = ft.Container(
            content=ft.Column([
                ft.Text("Create New Reward", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_200),
                ft.Row([item_name_input, item_cost_dropdown, add_btn], vertical_alignment=ft.CrossAxisAlignment.END)
            ]),
            padding=20,
            border=ft.Border.all(1, ft.Colors.GREY_800),
            border_radius=10,
            margin=ft.Margin.only(bottom=20)
        )

        def toggle_view(e):
            """
            Toggles between grid and list view modes.

            Takes:
              e (ft.ControlEvent): The event object.

            Gives:
              None.
            """
            self.view_mode = "grid" if self.view_mode == "list" else "list"
            self.view()

        view_toggle_btn = ft.IconButton(
            icon=ft.Icons.GRID_VIEW if self.view_mode == "list" else ft.Icons.LIST,
            tooltip="Toggle Grid/List View",
            on_click=toggle_view
        )

        def buy_item(item_id, name, cost):
            """
            Processes an item purchase confirmation.

            Takes:
              item_id (int): The ID of the item.
              name (str): The name of the item.
              cost (int): The cost of the item.

            Gives:
              None.
            """
            def confirm_buy(e):
                """
                Confirms the purchase and updates the UI.

                Takes:
                  e (ft.ControlEvent): The event object.

                Gives:
                  None.
                """
                if self.shop_service.buy_item(item_id, cost):
                    self.page.pop_dialog()
                    self.view()
                else:
                    snack = ft.SnackBar(ft.Text("Insufficient coins!"))
                    self.page.overlay.append(snack)
                    snack.open = True
                    self.page.update()

            dialog = ft.AlertDialog(
                title=ft.Text("Confirm Purchase"),
                content=ft.Text(f"Are you sure you want to purchase '{name}' for {cost} coins?"),
                actions=[
                    ft.TextButton("Cancel", on_click=lambda _: self.page.pop_dialog()),
                    ft.ElevatedButton("Buy", on_click=confirm_buy)
                ]
            )
            self.page.show_dialog(dialog)

        def remove_item(item_id, name):
            """
            Processes an item removal confirmation.

            Takes:
              item_id (int): The ID of the item.
              name (str): The name of the item.

            Gives:
              None.
            """
            def confirm_remove(e):
                """
                Confirms the removal and updates the UI.

                Takes:
                  e (ft.ControlEvent): The event object.

                Gives:
                  None.
                """
                self.shop_service.remove_item(item_id)
                self.page.pop_dialog()
                self.view()

            dialog = ft.AlertDialog(
                title=ft.Text("Remove Item"),
                content=ft.Text(f"Are you sure you want to remove '{name}' from the shop?"),
                actions=[
                    ft.TextButton("Cancel", on_click=lambda _: self.page.pop_dialog()),
                    ft.ElevatedButton("Remove", on_click=confirm_remove, bgcolor=ft.Colors.RED_700, color=ft.Colors.WHITE)
                ]
            )
            self.page.show_dialog(dialog)

        inventory_controls = []
        for item in items:
            iid, name, cost, count = item
            card_content = ft.Container(
                content=ft.Column([
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.CARD_GIFTCARD, color=ft.Colors.BLUE_400),
                        title=ft.Text(name, weight=ft.FontWeight.BOLD),
                        subtitle=ft.Text(f"Cost: {cost} coins | Purchased: {count} times")
                    ),
                    ft.Row([
                        ft.TextButton("Buy", icon=ft.Icons.SHOPPING_CART, on_click=lambda _, i=iid, n=name, c=cost: buy_item(i, n, c)),
                        ft.TextButton("Remove Item", icon=ft.Icons.DELETE_OUTLINE, icon_color=ft.Colors.RED_400, on_click=lambda _, i=iid, n=name: remove_item(i, n))
                    ], alignment=ft.MainAxisAlignment.END, spacing=10)
                ]),
                padding=10
            )
            
            if self.view_mode == "grid":
                inventory_controls.append(ft.Card(content=card_content, width=350))
            else:
                inventory_controls.append(ft.Card(content=card_content))

        if self.view_mode == "grid":
            inventory_view = ft.GridView(expand=True, controls=inventory_controls, max_extent=400, child_aspect_ratio=2.0, spacing=20, run_spacing=20)
        else:
            inventory_view = ft.ListView(expand=True, controls=inventory_controls, spacing=10)

        inventory_container = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text("Available Rewards", size=18, weight=ft.FontWeight.BOLD),
                    view_toggle_btn
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Divider(height=1, color=ft.Colors.GREY_800),
                ft.Container(content=inventory_view, expand=True)
            ], expand=True),
            expand=True
        )

        self.page.add(
            ft.Container(
                content=ft.Column([
                    header,
                    create_section,
                    inventory_container
                ], scroll=ft.ScrollMode.AUTO),
                padding=20,
                expand=True
            )
        )
        
        if WalletManager().is_bankrupt() == -1:
            dialog = ft.AlertDialog(
                title=ft.Text("Wallet Warning"),
                content=ft.Text("Your wallet balance is currently negative. You can try to recover by being more productive or declare bankruptcy by running 'zennify.sh --bankrupt' in your terminal."),
                actions=[ft.TextButton("Close", on_click=lambda e: self.page.pop_dialog())]
            )
            self.page.show_dialog(dialog)
