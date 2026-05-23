"""
File Name: main.py
Purpose: Direct traffic to the correct feature dashboard within the Zennify ecosystem.
"""

import sys
import flet as ft


def main(page: ft.Page):
    """
    Main entry point for the Flet application.
    Parses CLI arguments to route to the appropriate module.

    Takes: page (ft.Page)
    Gives: None
    """
    args = sys.argv[1:]
    
    if not args:
        page.add(ft.Text("Welcome to Zennify! Use CLI arguments to open specific modules."))
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
    elif mode == "--bankrupt":
        print("WARNING: You are about to declare bankruptcy.")
        print("This action is UNCHANGEABLE. You cannot go back.")
        print("Your wallet coins will be set to 0 and your bankrupt count will increment by 1.")
        try:
            confirm = input("Type 'yes' to declare bankruptcy, or 'no' to cancel: ")
            if confirm.strip().lower() == "yes":
                from core.shared.wallet import WalletManager
                WalletManager().declare_bankrupt()
                print("Bankruptcy declared successfully. Your wallet has been reset.")
            else:
                print("Action cancelled.")
        except EOFError:
            print("\nError: Terminal input required for bankruptcy declaration.")
    else:
        page.add(ft.Text(f"Unknown mode: {mode}"))


if __name__ == "__main__":
    ft.run(main)
