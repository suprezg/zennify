"""
File Name: wallet.py
Purpose: Manage wallet coins and bankruptcy across the Zennify ecosystem.
"""

from core.shared.storage import StorageManager


class WalletManager:
    """
    Manages the user's wallet, total coins, and bankruptcy state.
    """

    def __init__(self):
        """
        Initializes the WalletManager and connects to storage.

        Takes: None
        Gives: None
        """
        self.storage = StorageManager()

    def earn_coins(self, amount):
        """
        Updates the wallet's total coins. Prevents dropping below -75.

        Takes: amount (int)
        Gives: None
        """
        records = self.storage.read("SELECT total_coins FROM wallet WHERE id = 1")
        if records:
            current_coins = records[0][0]
            new_coins = current_coins + amount
            if new_coins < -75:
                new_coins = -75
            self.storage.write("UPDATE wallet SET total_coins = ? WHERE id = 1", (new_coins,))

    def declare_bankrupt(self):
        """
        Resets wallet to 0 and increments bankruptcy count.
        Note: The terminal interaction is handled in main.py, this method just updates DB.

        Takes: None
        Gives: None
        """
        records = self.storage.read("SELECT bankruptcy_count FROM wallet WHERE id = 1")
        if records:
            current_count = records[0][0]
            self.storage.write("UPDATE wallet SET total_coins = 0, bankruptcy_count = ? WHERE id = 1", (current_count + 1,))

    def is_bankrupt(self):
        """
        Checks if the wallet is in negative balance.

        Takes: None
        Gives: int (1 for positive/zero, -1 for negative)
        """
        records = self.storage.read("SELECT total_coins FROM wallet WHERE id = 1")
        if records:
            current_coins = records[0][0]
            if current_coins < 0:
                return -1
        return 1
