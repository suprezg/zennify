"""
File Name: main.py
Purpose: Direct traffic to the correct feature dashboard within the Zennify ecosystem.
"""

import sys
import os
import shutil
import flet as ft
from core.shared.configurator import ConfigManager


def show_help():
    """
    Prints the usage guide to the terminal for available CLI commands.

    Takes:
        None: Reads from hardcoded help strings.

    Gives:
        None: Outputs the help menu to the console.
    """
    print("\nZennify CLI - Usage Guide")
    print("=========================")
    print("\nOptions:")
    print("  --activity        Launch the Activity Tracking Dashboard")
    print("  --activity-popup  Launch the Activity Reward/Retribution Popup")
    print("  --flashcards      Launch the Flashcard Study Dashboard")
    print("  --todos           Launch the Todo Management Dashboard")
    print("  --pomodoro        Launch the Pomodoro Timer Dashboard")
    print("  --shop            Launch the Reward Shop")
    print("  --bankrupt        Initiate the Bankruptcy declaration process")
    print("  --backup <path>   Create a backup of the database at the specified path")
    print("  --restore <path>  Restore the database from a backup file")
    print("  --help            Show this help message")


def main(page: ft.Page):
    """
    Main entry point for the Flet application that routes to specific GUI modules.

    Takes:
        page (ft.Page): The root page object provided by the Flet framework for UI rendering.

    Gives:
        None: Initializes and displays the requested module's view.
    """
    args = sys.argv[1:]
    
    if not args:
        return

    mode = args[0]
    
    if mode == "--activity":
        from core.activity.dashboard import ActivityDashboard
        ActivityDashboard(page).view()
    elif mode == "--activity-popup":
        from core.activity.popup import ActivityPopup
        ActivityPopup(page).view()
    elif mode == "--flashcards":
        from core.flashcards.dashboard import FlashcardDashboard
        FlashcardDashboard(page).view()
    elif mode == "--todos":
        from core.todos.dashboard import TodoDashboard
        TodoDashboard(page).view()
    elif mode == "--pomodoro":
        from core.pomodoro.dashboard import PomodoroDashboard
        PomodoroDashboard(page).view()
    elif mode == "--shop":
        from core.shop.dashboard import ShopDashboard
        ShopDashboard(page).view()


if __name__ == "__main__":
    args = sys.argv[1:]
    
    gui_modes = [
        "--activity", 
        "--activity-popup", 
        "--flashcards", 
        "--todos", 
        "--pomodoro", 
        "--shop"
    ]
    
    if not args or args[0] == "--help":
        show_help()
    elif args[0] == "--bankrupt":
        from core.shared.wallet import WalletManager
        WalletManager().declare_bankrupt()
    elif args[0] == "--backup":
        if len(args) < 2:
            print("Error: --backup requires a destination path.")
            sys.exit(1)
            
        backup_path = args[1]
        db_path = ConfigManager().read_value("system", "database_path")
        
        if not db_path or not os.path.exists(db_path):
            print("Error: Database file not found.")
            sys.exit(1)
            
        try:
            shutil.copy2(db_path, backup_path)
            print(f"Backup created successfully at '{backup_path}'.")
        except Exception as e:
            print(f"Error creating backup: {e}")
            sys.exit(1)
    elif args[0] == "--restore":
        if len(args) < 2:
            print("Error: --restore requires a path to the backup file.")
            sys.exit(1)
            
        backup_path = args[1]
        if not os.path.exists(backup_path):
            print(f"Error: Backup file not found at '{backup_path}'.")
            sys.exit(1)
            
        confirm = input(f"Are you sure you want to restore the database from '{backup_path}'? This will overwrite the current database. [y/n]: ")
        if confirm.lower() == 'y':
            db_path = ConfigManager().read_value("system", "database_path")
            if db_path:
                shutil.copy2(backup_path, db_path)
                print("Database restored successfully.")
            else:
                print("Error: Could not retrieve the current database path from configuration.")
                sys.exit(1)
        else:
            print("Restore cancelled.")
    elif args[0] in gui_modes:
        ft.run(main)
    else:
        show_help()
