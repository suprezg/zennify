"""
File Name: main.py
Purpose: Direct traffic to the correct feature dashboard within the Zennify ecosystem.
"""

import sys
import flet as ft


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
    elif args[0] in gui_modes:
        ft.run(main)
    else:
        show_help()
