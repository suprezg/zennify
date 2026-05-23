"""
File Name: dashboard.py
Purpose: User interface for the Pomodoro feature.
"""

import datetime
import io
import base64
import asyncio
import flet as ft
import matplotlib
import matplotlib.pyplot as plt
from core.pomodoro.service import PomodoroTimer, PomodoroSettings, PomodoroStatistics
from core.shared.wallet import WalletManager

matplotlib.use("agg")


class PomodoroDashboard:
    """
    Main dashboard class for the Pomodoro feature.
    """

    def __init__(self, page):
        """
        Initializes the dashboard with the Flet page and services.

        Takes: page (ft.Page)
        Gives: None
        """
        self.page = page
        self.timer_service = PomodoroTimer()
        self.settings_service = PomodoroSettings()
        self.stats_service = PomodoroStatistics()
        self.wallet_manager = WalletManager()
        self.timer_running = False

    def view(self, selected_index=0):
        """
        Builds and displays the main view for the pomodoro dashboard.

        Takes: selected_index (int)
        Gives: None
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

        if self.wallet_manager.is_bankrupt() == -1:
            dialog = ft.AlertDialog(
                title=ft.Text("Wallet Warning"),
                content=ft.Text("Your wallet balance is currently negative. You can try to recover by being more productive or declare bankruptcy by running 'zennify.sh --bankrupt' in your terminal."),
                actions=[ft.TextButton("Close", on_click=lambda e: self.page.pop_dialog())]
            )
            self.page.show_dialog(dialog)

    def _timer_tab(self):
        """
        Builds the Timer tab UI.

        Takes: None
        Gives: ft.Column
        """
        config = self.settings_service.read_config()
        state = self.timer_service.get_current_state()
        
        phase_label = ft.Text(state["phase"], size=32, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_200)
        timer_text = ft.Text(self._format_seconds(state["remaining_seconds"]), size=80, weight=ft.FontWeight.BOLD)
        
        # Info Box
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
                timer_text.value = self._format_seconds(state["remaining_seconds"])
                phase_label.value = state["phase"]
                
                if state["remaining_seconds"] == 0 and state["is_running"] == False:
                    # Mark complete in DB if it was Work
                    if state["phase"] == "Work":
                        duration = int(self.timer_service._parse_time(config["work_time"]) / 60)
                        self.timer_service.mark_complete(duration)
                    
                    # Alert and switch phase
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
            ft.Container(height=40),
            info_box,
            ft.Container(height=40),
            phase_label,
            timer_text,
            ft.Container(height=20),
            ft.Row([start_btn, pause_btn, stop_btn, restart_btn], alignment=ft.MainAxisAlignment.CENTER, spacing=15),
            ft.Container(height=40),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, scroll=ft.ScrollMode.AUTO)

    def _format_seconds(self, seconds):
        mins, secs = divmod(seconds, 60)
        return f"{int(mins):02d}:{int(secs):02d}"

    def _overview_tab(self):
        """
        Builds the Overview tab UI.

        Takes: None
        Gives: ft.Column
        """
        data = self.stats_service.give_overview()

        metrics_row = ft.Row(
            [
                ft.Column([ft.Icon(ft.Icons.SPA, color=ft.Colors.BLUE_400), ft.Text(f"Zen Time: {data['total_zen_time']}", weight=ft.FontWeight.BOLD)], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Column([ft.Icon(ft.Icons.TRACK_CHANGES, color=ft.Colors.AMBER_400), ft.Text(f"Avg Daily: {data['avg_daily_focus']}m", weight=ft.FontWeight.BOLD)], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            ],
            alignment=ft.MainAxisAlignment.CENTER, spacing=60
        )

        bg_color = "#111418"
        plt.rcParams.update({
            "text.color": "white",
            "axes.labelcolor": "white",
            "xtick.color": "white",
            "ytick.color": "white",
            "axes.edgecolor": "white"
        })

        def fig_to_base64(fig):
            buf = io.BytesIO()
            fig.tight_layout(pad=1.5)
            fig.savefig(buf, format="png", bbox_inches="tight", facecolor=bg_color, dpi=100)
            plt.close(fig)
            return base64.b64encode(buf.getvalue()).decode("utf-8")

        # 1. Day of Week (Bar Chart)
        fig1, ax1 = plt.subplots(figsize=(7, 4))
        ax1.set_facecolor(bg_color)
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        ax1.bar(days, data['dow_data'], color="#42A5F5")
        chart1_base64 = fig_to_base64(fig1)

        # 2. Session Distribution (Pie Chart)
        fig2, ax2 = plt.subplots(figsize=(7, 4))
        ax2.set_facecolor(bg_color)
        raw_labels = list(data['session_dist'].keys())
        raw_values = list(data['session_dist'].values())
        labels = [l for l, v in zip(raw_labels, raw_values) if v > 0]
        values = [v for v in raw_values if v > 0]
        if sum(values) > 0:
            # 3. Zip colors dynamically to match only the active categories
            all_colors = ["#66BB6A", "#FFA726", "#EF5350"]
            colors = [c for c, v in zip(all_colors, raw_values) if v > 0]
            
            ax2.pie(values, labels=labels, autopct='%1.1f%%', colors=colors, textprops={'color':"w"})
        else:
            ax2.text(0.5, 0.5, "No Data", ha='center', va='center')

        chart2_base64 = fig_to_base64(fig2)

        # 3. Trend Analysis (Line Chart)
        fig3, ax3 = plt.subplots(figsize=(7, 4))
        ax3.set_facecolor(bg_color)
        if data['trend_data']:
            dates, mins = zip(*data['trend_data'])
            short_dates = [d[-5:] for d in dates]
            ax3.plot(short_dates, mins, color="#FFCA28", marker="o", linewidth=2)
            for i, t in enumerate(ax3.get_xticklabels()):
                if i % 5 != 0: t.set_visible(False)
        else:
            ax3.text(0.5, 0.5, "No Data", ha='center', va='center')
        chart3_base64 = fig_to_base64(fig3)

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

        # 24h Heatmap (Simple visual using ft.Row of colored boxes)
        heatmap_24h = ft.Row([
            ft.Container(width=20, height=20, bgcolor=self._get_heat_color(val), tooltip=f"Hour {i}: {val}m") 
            for i, val in enumerate(data['heatmap_24h'])
        ], spacing=2, alignment=ft.MainAxisAlignment.CENTER)

        return ft.Column([
            ft.Container(content=metrics_row, padding=20),
            ft.Divider(height=1, color=ft.Colors.GREY_800),
            ft.Container(
                content=ft.Column([
                    ft.Text("24-Hour Focus Distribution", size=16, weight=ft.FontWeight.BOLD),
                    heatmap_24h,
                    ft.Text("Shows which hours of the day you log the most focus time.", size=12, color=ft.Colors.GREY_400)
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=20
            ),
            row_builder(
                "Day-of-Week Comparison",
                ft.Image(src=chart1_base64, height=300, fit=ft.BoxFit.CONTAIN),
                "Compares your total focus time across different days of the week. Helps identify your most and least productive days.",
                "Identify your 'Warrior' days and try to replicate that focus on 'Slacker' days."
            ),
            row_builder(
                "Session Distribution",
                ft.Image(src=chart2_base64, height=300, fit=ft.BoxFit.CONTAIN),
                "Categorizes your sessions by length: Deep Focus (>50m), Standard (~25m), and Short Bursts. More Deep Focus indicates better flow state.",
                "Aim for a higher percentage of 'Deep Focus' sessions for complex tasks."
            ),
            row_builder(
                "Focus Trend (Last 30 Days)",
                ft.Image(src=chart3_base64, height=300, fit=ft.BoxFit.CONTAIN),
                "Tracks your daily focus volume over time. Useful for spotting burnout or growing productivity habits.",
                "Watch for downward trends which might signal a need for more rest."
            )
        ], expand=True, scroll=ft.ScrollMode.AUTO, spacing=40)

    def _get_heat_color(self, val):
        if val == 0: return ft.Colors.GREY_900
        if val < 30: return ft.Colors.BLUE_200
        if val < 60: return ft.Colors.BLUE_400
        return ft.Colors.BLUE_700

    def _settings_tab(self):
        """
        Builds the Settings tab UI.

        Takes: None
        Gives: ft.Container
        """
        config = self.settings_service.read_config()
        
        work_drop = ft.Dropdown(label="Work Time", options=[ft.dropdown.Option(o) for o in ["30m", "60m", "90m", "120m"]], value=config["work_time"], width=200)
        short_drop = ft.Dropdown(label="Short Break", options=[ft.dropdown.Option(o) for o in ["5m", "10m", "15m"]], value=config["short_break_time"], width=200)
        long_drop = ft.Dropdown(label="Long Break", options=[ft.dropdown.Option(o) for o in ["10m", "15m", "20m", "25m", "30m"]], value=config["long_break_time"], width=200)
        interval_drop = ft.Dropdown(label="Long Break Interval", options=[ft.dropdown.Option(str(i)) for i in range(1, 11)], value=str(config["long_break_interval"]), width=200)

        def save_settings(e):
            self.settings_service.change_preset("work_time", work_drop.value)
            self.settings_service.change_preset("short_break_time", short_drop.value)
            self.settings_service.change_preset("long_break_time", long_drop.value)
            self.settings_service.change_preset("long_break_interval", interval_drop.value)
            
            # Reset timer state to match new work time
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
