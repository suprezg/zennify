"""
File Name: wallet.py
Purpose: Manage wallet coins and bankruptcy across the Zennify ecosystem.
"""

from core.shared.storage import StorageManager


class WalletManager:
    """
    Manages the user's wallet, total coins, and bankruptcy state.
    Provides methods to earn coins, check bankruptcy status, and reset the wallet.
    """

    def __init__(self):
        """
        Initializes the WalletManager and establishes a connection to the storage service.

        Takes:
            None: Operates on the internal storage manager instance.

        Gives:
            None: Initializes the 'storage' attribute.
        """
        self.storage = StorageManager()

    def earn_coins(self, amount):
        """
        Updates the wallet's total coin balance, enforcing a minimum debt limit.

        Takes:
            amount (float/int): The number of coins to add to (or subtract from) the wallet.

        Gives:
            None: Updates the database record for the wallet.
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
        Interactively prompts the user to reset their wallet and increment bankruptcy count.

        Takes:
            None: Requires user interaction via terminal input.

        Gives:
            None: Updates the database and prints status messages to the console.
        """
        print("WARNING: You are about to declare bankruptcy.")
        print("This action is UNCHANGEABLE. You cannot go back.")
        print("Your wallet coins will be set to 0 and your bankrupt count will increment by 1.")
        try:
            confirm = input("Type 'yes' to declare bankruptcy, or 'no' to cancel: ")
            if confirm.strip().lower() == "yes":
                records = self.storage.read("SELECT bankruptcy_count FROM wallet WHERE id = 1")
                if records:
                    current_count = records[0][0]
                    self.storage.write("UPDATE wallet SET total_coins = 0, bankruptcy_count = ? WHERE id = 1", (current_count + 1,))
                print("Bankruptcy declared successfully. Your wallet has been reset.")
            else:
                print("Action cancelled.")
        except EOFError:
            print("\nError: Terminal input required for bankruptcy declaration.")

    def is_bankrupt(self):
        """
        Checks the current balance to determine if the user is in a state of bankruptcy.

        Takes:
            None: Queries the storage manager for the wallet's current balance.

        Gives:
            int: Returns -1 if the balance is negative, otherwise returns 1.
        """
        records = self.storage.read("SELECT total_coins FROM wallet WHERE id = 1")
        if records:
            current_coins = records[0][0]
            if current_coins < 0:
                return -1
        return 1
