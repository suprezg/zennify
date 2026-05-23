"""
File Name: popup.py
Purpose: Interactive popup for logging activity entries with streak and multiplier logic.
"""

import datetime
import asyncio
import flet as ft
from core.activity.service import ActivitySettings, ActivityStorage
from core.shared.configurator import ConfigManager
from core.shared.wallet import WalletManager


class ActivityPopup:
    """
    Main popup class for the Activity logger.
    """

    def __init__(self, page):
        """
        Initializes the popup with Flet page and services.

        Takes: page (ft.Page)
        Gives: None
        """
        self.page = page
        self.settings_service = ActivitySettings()
        self.config_manager = ConfigManager()
        self.storage_service = ActivityStorage()
        self.wallet_manager = WalletManager()
        
        interval_timer = self.config_manager.read_value("activity", "popup_interval_timer") or "30m"
        visible_timer = self.config_manager.read_value("activity", "popup_visible_timer") or "1m"
        self.interval_seconds = self._parse_timer(interval_timer)
        self.visible_seconds = self._parse_timer(visible_timer)
        
        self.current_time = datetime.datetime.now()
        self.start_time = self.current_time - datetime.timedelta(seconds=self.interval_seconds)
        
        self.timer_text = ft.Text(size=14, weight=ft.FontWeight.W_500, color=ft.Colors.AMBER)
        self.description_input = ft.TextField(label="What were you doing?", expand=True)
        
        recent_tags = self.storage_service.get_recent_tags()
        self.tag_dropdown = ft.Dropdown(
            label="Select Tag",
            options=[ft.dropdown.Option(tag) for tag in recent_tags],
            expand=True
        )
        self.new_tag_input = ft.TextField(label="Or new tag", expand=True)
        
        self.productivity_radio = ft.RadioGroup(
            content=ft.Row(
                [
                    ft.Radio(value="productive", label="Productive"),
                    ft.Radio(value="unproductive", label="Unproductive"),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=20
            ),
            value="productive"
        )

    def view(self):
        """
        Configures and displays the popup window.

        Takes: None
        Gives: None
        """
        self.page.title = "Zennify - Log Activity"
        self.page.theme_mode = ft.ThemeMode.DARK
        
        self.page.window.width = 450
        self.page.window.height = 550
        self.page.window.min_width = 450
        self.page.window.min_height = 550
        self.page.window.always_on_top = True
        
        self.page.add(
            ft.Container(
                content=ft.Column(
                    [
                        ft.Row([ft.Icon(ft.Icons.TIMER), self.timer_text], alignment=ft.MainAxisAlignment.CENTER),
                        ft.Text(
                            f"Logging activity from {self.start_time.strftime('%H:%M')} to {self.current_time.strftime('%H:%M')}",
                            size=16,
                            weight=ft.FontWeight.BOLD,
                            text_align=ft.TextAlign.CENTER
                        ),
                        self.description_input,
                        ft.Row([self.tag_dropdown, self.new_tag_input], spacing=10),
                        ft.Text("Was this interval productive?", size=14, weight=ft.FontWeight.W_500),
                        self.productivity_radio,
                        ft.Button(
                            "Log Activity",
                            on_click=lambda e: self._submit(),
                            width=200,
                            height=45,
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
                        )
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=20,
                    expand=True
                ),
                padding=20,
                expand=True
            )
        )
        
        self.page.run_task(self._countdown_timer)

    async def _countdown_timer(self):
        """
        Async task to handle the countdown and auto-submission.

        Takes: None
        Gives: None
        """
        remaining = self.visible_seconds
        while remaining > 0:
            mins, secs = divmod(remaining, 60)
            self.timer_text.value = f"Time Remaining: {mins:02d}:{secs:02d}"
            self.page.update()
            await asyncio.sleep(1)
            remaining -= 1
        
        self._submit(auto=True)

    def _submit(self, auto=False):
        """
        Calculates rewards and logs the entry to the database.

        Takes: auto (bool)
        Gives: None
        """
        if auto:
            description = "Inactive"
            tag = "Inactive"
            is_productive = False
        else:
            description = self.description_input.value or "No description"
            tag = self.new_tag_input.value or self.tag_dropdown.value or "None"
            is_productive = self.productivity_radio.value == "productive"

        streak = self.config_manager.read_value("activity", "streak") or 0
        multiplier = self.config_manager.read_value("activity", "multiplier") or 1.0
        
        if is_productive:
            last_entry = self.storage_service.get_last_entry()
            if last_entry and last_entry[6]:
                multiplier = min(2.0, multiplier + 0.1)
                streak += 1
            else:
                multiplier = 1.0
                streak = 1
            
            retribution = int(5 * multiplier)
        else:
            streak = 0
            multiplier = 1.0
            retribution = -2
        
        self.storage_service.write_entry(
            self.current_time.strftime("%Y-%m-%d"),
            self.start_time.strftime("%H:%M"),
            self.current_time.strftime("%H:%M"),
            description,
            tag,
            is_productive,
            retribution
        )
        
        self.wallet_manager.earn_coins(retribution)
        self.settings_service.update_streak_data(streak, round(multiplier, 1))
        
        self.page.run_task(self.page.window.destroy)

    def _parse_timer(self, timer_str):
        """
        Parses timer strings like '30m' or '1h' into seconds.

        Takes: timer_str (str)
        Gives: int
        """
        try:
            val = int(timer_str[:-1])
            unit = timer_str[-1].lower()
            if unit == 'm':
                return val * 60
            elif unit == 'h':
                return val * 3600
            return val
        except (ValueError, IndexError):
            return 60
