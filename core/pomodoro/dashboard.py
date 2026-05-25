"""
File Name: dashboard.py
Purpose: User interface for the Pomodoro feature.
"""

import datetime
import io
import base64
import asyncio
import flet as ft
from core.pomodoro.service import PomodoroTimer, PomodoroSettings, PomodoroStatistics


class PomodoroDashboard:
    """
    Main dashboard class for the Pomodoro feature.
    Manages the user interface for the timer, statistics overview, and settings configuration.
    """

    def __init__(self, page):
        """
        Initializes the dashboard with the Flet page and necessary service instances.

        Takes:
          page (ft.Page): The root page object for rendering the Flet application.

        Gives:
          None.
        """
        self.page = page
        self.timer_service = PomodoroTimer()
        self.settings_service = PomodoroSettings()
        self.stats_service = PomodoroStatistics()
        self.timer_running = False

    def view(self, selected_index=0):
        """
        Builds and displays the main tabbed view for the Pomodoro dashboard.

        Takes:
          selected_index (int): The index of the tab to be selected upon loading (default is 0).

        Gives:
          None.
        """
        self.page.title = "Zennify - Pomodoro Timer"
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.window.min_width = 800
        self.page.window.min_height = 600
        self.page.clean()

        tabs = ft.Tabs(
            length=3,
            selected_index=selected_index,
            animation_duration=300,
            expand=True,
            content=ft.Column(
                expand=True,
                controls=[
                    ft.TabBar(
                        tabs=[
                            ft.Tab(label="Timer"),
                            ft.Tab(label="Overview"),
                            ft.Tab(label="Settings"),
                        ]
                    ),
                    ft.TabBarView(
                        expand=True,
                        controls=[
                            self._timer_tab(),
                            self._overview_tab(),
                            self._settings_tab(),
                        ],
                    ),
                ],
            ),
        )

        self.page.add(tabs)

    def _timer_tab(self):
        """
        Builds the Timer tab UI, providing visual feedback and controls for Pomodoro sessions.

        Takes:
          None.

        Gives:
          ft.Column: A column control containing the info box, phase label, timer text, and action buttons.
        """
        config = self.settings_service.get_preset()
        state = self.timer_service.get_current_state()
        
        def format_seconds(seconds):
            mins, secs = divmod(seconds, 60)
            return f"{int(mins):02d}:{int(secs):02d}"


        phase_label = ft.Text(state["phase"], size=32, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_200)
        timer_text = ft.Text(format_seconds(state["remaining_seconds"]), size=80, weight=ft.FontWeight.BOLD)
        
        info_box = ft.Container(
            content=ft.Column([
                ft.Text("CURRENT PRESETS", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_400),
                ft.Row([
                    ft.Column([ft.Text("Work", size=12), ft.Text(config["work_time"], weight=ft.FontWeight.BOLD)]),
                    ft.VerticalDivider(),
                    ft.Column([ft.Text("Short", size=12), ft.Text(config["short_break_time"], weight=ft.FontWeight.BOLD)]),
                    ft.VerticalDivider(),
                    ft.Column([ft.Text("Long", size=12), ft.Text(config["long_break_time"], weight=ft.FontWeight.BOLD)]),
                    ft.VerticalDivider(),
                    ft.Column([ft.Text("Interval", size=12), ft.Text(str(config["long_break_interval"]), weight=ft.FontWeight.BOLD)]),
                ], spacing=20, alignment=ft.MainAxisAlignment.CENTER)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=20, border=ft.Border.all(1, ft.Colors.GREY_800), border_radius=10
        )

        async def update_timer():
            while True:
                state = self.timer_service.get_current_state()
                timer_text.value = format_seconds(state["remaining_seconds"])
                phase_label.value = state["phase"]
                
                if state["remaining_seconds"] == 0 and state["is_running"] == False:
                    if state["phase"] == "Work":
                        duration = int(self.timer_service._parse_time(config["work_time"]) / 60)
                        self.timer_service.mark_complete(duration)
                    
                    def on_ok(e):
                        self.timer_service.change_phase()
                        self.page.pop_dialog()
                        self.view(0)

                    dialog = ft.AlertDialog(
                        modal=True,
                        title=ft.Text("Phase Complete"),
                        content=ft.Text(f"{state['phase']} session finished! Ready for the next phase?"),
                        actions=[ft.TextButton("Okay", on_click=on_ok)]
                    )
                    self.page.show_dialog(dialog)
                    break
                
                if not state["is_running"]:
                    break
                    
                self.page.update()
                await asyncio.sleep(1)

        def on_start(e):
            self.timer_service.start()
            start_btn.visible = False
            pause_btn.visible = True
            stop_btn.visible = True
            self.page.run_task(update_timer)
            self.page.update()

        def on_pause(e):
            self.timer_service.pause()
            start_btn.text = "Resume"
            start_btn.visible = True
            pause_btn.visible = False
            self.page.update()

        def on_stop(e):
            self.timer_service.stop()
            start_btn.text = "Start"
            start_btn.visible = True
            pause_btn.visible = False
            stop_btn.visible = False
            self.view(0)

        def on_restart(e):
            self.timer_service.restart()
            self.view(0)

        start_btn = ft.Button("Start", on_click=on_start, height=50, width=120, bgcolor=ft.Colors.BLUE_700, color=ft.Colors.WHITE)
        pause_btn = ft.Button("Pause", on_click=on_pause, height=50, width=120, bgcolor=ft.Colors.AMBER_700, color=ft.Colors.WHITE, visible=False)
        stop_btn = ft.Button("Stop", on_click=on_stop, height=50, width=120, bgcolor=ft.Colors.RED_700, color=ft.Colors.WHITE, visible=False)
        restart_btn = ft.Button("Restart", on_click=on_restart, height=50, width=120, bgcolor=ft.Colors.GREY_700, color=ft.Colors.WHITE)

        if state["is_running"]:
            start_btn.visible = False
            pause_btn.visible = True
            stop_btn.visible = True
            self.page.run_task(update_timer)
        elif state["remaining_seconds"] < self.timer_service._parse_time(config["work_time"]) if state["phase"] == "Work" else True:
             if state["remaining_seconds"] > 0:
                start_btn.text = "Resume"
                stop_btn.visible = True

        return ft.Column([
            info_box,
            ft.Container(height=40),
            phase_label,
            timer_text,
            ft.Container(height=20),
            ft.Row([start_btn, pause_btn, stop_btn, restart_btn], alignment=ft.MainAxisAlignment.CENTER, spacing=15),
            ft.Container(height=40),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, scroll=ft.ScrollMode.AUTO)

    def _overview_tab(self):
        """
        Builds the Overview tab UI, displaying productivity metrics and statistical charts.

        Takes:
          None.

        Gives:
          ft.Column: A scrollable column containing standardized metric and chart cards.
        """
        overview_data = self.stats_service.give_overview()

        def row_builder(title, visual_content, explanation, insight):
            return ft.Row([
                ft.Container(
                    content=ft.Column([
                        ft.Text(title, size=16, weight=ft.FontWeight.BOLD),
                        visual_content
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    expand=3, border=ft.Border.all(2, ft.Colors.WHITE), border_radius=10, padding=10
                ),
                ft.Container(
                    content=ft.Column([
                        ft.Text("About this Metric", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_200),
                        ft.Text(explanation, size=14, color=ft.Colors.GREY_300),
                        ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
                        ft.Text(insight, size=15, weight=ft.FontWeight.W_500, color=ft.Colors.AMBER_ACCENT)
                    ], spacing=10),
                    expand=2, padding=30, alignment=ft.Alignment.TOP_LEFT
                )
            ], vertical_alignment=ft.CrossAxisAlignment.START, spacing=20)

        rows = []
        for item in overview_data:
            if item["type"] == "text":
                visual = ft.Container(
                    content=ft.Text(item["value"], size=50, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_ACCENT), 
                    height=300, 
                    alignment=ft.Alignment.CENTER
                )
            else:
                visual = ft.Image(src=item["image_base64"], height=300, fit=ft.BoxFit.CONTAIN)
            
            rows.append(
                row_builder(
                    item["title"],
                    visual,
                    item["explanation"],
                    item["insight"]
                )
            )

        if not rows:
            return ft.Column([
                ft.Container(height=100),
                ft.Text("No data available yet. Start some Pomodoro sessions to see statistics!", size=20, italic=True, color=ft.Colors.GREY_400)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True)

        return ft.Column(rows, expand=True, scroll=ft.ScrollMode.AUTO, spacing=40)

    def _settings_tab(self):
        """
        Builds the Settings tab UI for configuring Pomodoro durations and intervals.

        Takes:
          None.

        Gives:
          ft.Container: A container with the configuration dropdowns and save button.
        """
        config = self.settings_service.get_preset()
        
        work_drop = ft.Dropdown(label="Work Time", options=[ft.dropdown.Option(o) for o in ["30m", "60m", "90m", "120m"]], value=config["work_time"], width=200)
        short_drop = ft.Dropdown(label="Short Break", options=[ft.dropdown.Option(o) for o in ["5m", "10m", "15m"]], value=config["short_break_time"], width=200)
        long_drop = ft.Dropdown(label="Long Break", options=[ft.dropdown.Option(o) for o in ["10m", "15m", "20m", "25m", "30m"]], value=config["long_break_time"], width=200)
        interval_drop = ft.Dropdown(label="Long Break Interval", options=[ft.dropdown.Option(str(i)) for i in range(1, 11)], value=str(config["long_break_interval"]), width=200)

        def save_settings(e):
            self.settings_service.change_preset(work_drop.value, short_drop.value, long_drop.value, interval_drop.value)
            
            self.timer_service.state["phase"] = "Work"
            self.timer_service.state["completed_pomodoros"] = 0
            self.timer_service.stop()
            
            snack = ft.SnackBar(ft.Text("Settings saved! Timer reset."))
            self.page.overlay.append(snack)
            snack.open = True
            self.view(2)
            self.page.update()

        return ft.Container(
            content=ft.Column([
                ft.Text("Pomodoro Presets", size=18, weight=ft.FontWeight.BOLD),
                work_drop, short_drop, long_drop, interval_drop,
                ft.Button("Save Settings", on_click=save_settings, height=50)
            ], spacing=20),
            padding=30, alignment=ft.Alignment.TOP_LEFT
        )
