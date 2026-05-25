"""
File Name: service.py
Purpose: Logic and data management for the Shop feature.
"""

from core.shared.storage import StorageManager
from core.shared.configurator import ConfigManager
from core.shared.wallet import WalletManager


class ShopMain:
    """
    Business logic for the Shop module, including inventory and bankruptcy.
    """

    def __init__(self):
        """
        Initializes the shop service and its dependencies.

        Takes:
          None.

        Gives:
          None.
        """
        self.storage = StorageManager()
        self.config_manager = ConfigManager()
        self.wallet_manager = WalletManager()

    def give_wallet_details(self):
        """
        Retrieves current coins and bankruptcy count.

        Takes:
          None.

        Gives:
          tuple: Current coins and bankruptcy count.
        """
        records = self.storage.read("SELECT total_coins, bankruptcy_count FROM wallet WHERE id = 1")
        if records:
            return records[0]
        return (0, 0)

    def get_items(self):
        """
        Retrieves all items from the shop.

        Takes:
          None.

        Gives:
          list: List of shop items.
        """
        return self.storage.read("SELECT * FROM shop ORDER BY item_id DESC")

    def add_item(self, name, cost):
        """
        Adds a new custom item to the shop.

        Takes:
          name (str): The name of the item.
          cost (int): The cost of the item.

        Gives:
          None.
        """
        self.storage.write(
            "INSERT INTO shop (item_name, cost, purchase_count) VALUES (?, ?, ?)",
            (name, cost, 0)
        )

    def remove_item(self, item_id):
        """
        Removes an item from the shop.

        Takes:
          item_id (int): The ID of the item to remove.

        Gives:
          None.
        """
        self.storage.write("DELETE FROM shop WHERE item_id = ?", (item_id,))

    def buy_item(self, item_id, cost):
        """
        Processes an item purchase if funds are sufficient.

        Takes:
          item_id (int): The ID of the item to buy.
          cost (int): The cost of the item.

        Gives:
          bool: True if successful, False otherwise.
        """
        details = self.give_wallet_details()
        if details[0] >= cost:
            self.wallet_manager.earn_coins(-cost)
            self.storage.write(
                "UPDATE shop SET purchase_count = purchase_count + 1 WHERE item_id = ?",
                (item_id,)
            )
            return True
        return False

    def declare_bankrupt(self):
        """
        Executes a full bankruptcy: resets coins, increments count, and resets all streaks.

        Takes:
          None.

        Gives:
          None.
        """
        self.wallet_manager.declare_bankrupt()

        for feature in ["activity", "todo", "flashcard"]:
            self.config_manager.update_value(feature, "streak", 0)
            self.config_manager.update_value(feature, "multiplier", 1.0)
