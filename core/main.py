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
        from core.flashcards.dashboard import FlashcardsDashboard
        FlashcardsDashboard(page).view()
    elif mode == "--todos":
        from core.todos.dashboard import TodoDashboard
        TodoDashboard(page).view()
    elif mode == "--pomodoro":
        from core.pomodoro.dashboard import PomodoroDashboard
        PomodoroDashboard(page).view()
    elif mode == "--shop":
        from core.shop.dashboard import ShopDashboard
        ShopDashboard(page).view()
    elif mode == "--reset":
        # TBD
    elif mode == "--bankrupt":
        # TBD
    else:
        page.add(ft.Text(f"Unknown mode: {mode}"))


if __name__ == "__main__":
    ft.app(target=main)
