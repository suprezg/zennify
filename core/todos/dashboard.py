"""
File Name: dashboard.py
Purpose: User interface for the Todos feature with hardcore deadline management.
"""

import datetime
import io
import base64
import flet as ft
import matplotlib
import matplotlib.pyplot as plt
from core.todos.service import TodoTasks, TodoSettings, TodoStatistics
from core.shared.wallet import WalletManager

matplotlib.use("agg")


class TodoDashboard:
    """
    Main dashboard class for the Todo feature.
    """

    def __init__(self, page):
        """
        Initializes the dashboard with the Flet page and services.

        Takes: page (ft.Page)
        Gives: None
        """
        self.page = page
        self.tasks_service = TodoTasks()
        self.settings_service = TodoSettings()
        self.stats_service = TodoStatistics()
        self.wallet_manager = WalletManager()

        self.current_month = datetime.datetime.now().strftime("%m")
        self.current_year = datetime.datetime.now().strftime("%Y")

    def view(self, selected_index=0):
        """
        Builds and displays the main view for the todo dashboard.

        Takes: selected_index (int)
        Gives: None
        """
        self.page.title = "Zennify - Hardcore Todos"
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
                            ft.Tab(label="Tasks"),
                            ft.Tab(label="Overview"),
                            ft.Tab(label="Settings"),
                        ]
                    ),
                    ft.TabBarView(
                        expand=True,
                        controls=[
                            self._tasks_tab(),
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

    def _tasks_tab(self):
        """
        Builds the Tasks tab UI.

        Takes: None
        Gives: ft.Column
        """
        # Task Input
        task_name_input = ft.TextField(hint_text="e.g., Complete Project Documentation", expand=True)
        deadline_date = datetime.datetime.now()

        def on_date_change(e):
            nonlocal deadline_date
            if date_picker.value:
                deadline_date = date_picker.value.astimezone()
                date_btn.content = deadline_date.strftime("%Y-%m-%d")
                date_btn.update()

        date_picker = ft.DatePicker(
            on_change=on_date_change,
            first_date=datetime.datetime.now() - datetime.timedelta(days=2),
            last_date=datetime.datetime.now() + datetime.timedelta(days=365)
        )
        
        date_btn = ft.Button(
            content=deadline_date.strftime("%Y-%m-%d"),
            icon=ft.Icons.CALENDAR_MONTH,
            on_click=lambda _: self.page.show_dialog(date_picker),
            height=50
        )

        def add_task(e):
            if not task_name_input.value: return
            success, msg = self.tasks_service.add_task(task_name_input.value, deadline_date.isoformat())
            if not success:
                snack = ft.SnackBar(ft.Text(msg))
                self.page.overlay.append(snack)
                snack.open = True
            else:
                task_name_input.value = ""
                self.view(0)
            self.page.update()

        add_btn = ft.IconButton(icon=ft.Icons.ADD_CIRCLE, on_click=add_task, icon_color=ft.Colors.GREEN_ACCENT, icon_size=35)

        # Running Tasks List
        running_tasks = self.tasks_service.list_running_tasks()
        tasks_list = ft.ListView(expand=True, spacing=10)
        
        for tid, name, ddl in running_tasks:
            def mark_comp(e, task_id=tid):
                self.tasks_service.mark_task(task_id, "Completed")
                self.view(0)

            tasks_list.controls.append(
                ft.ListTile(
                    leading=ft.Icon(ft.Icons.TASK_ALT, color=ft.Colors.BLUE_400),
                    title=ft.Text(name, weight=ft.FontWeight.BOLD),
                    subtitle=ft.Text(f"Deadline: {ddl[:10]}"),
                    trailing=ft.IconButton(ft.Icons.CHECK, on_click=mark_comp, icon_color=ft.Colors.GREEN_ACCENT),
                    bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.WHITE)
                )
            )

        # Heatmap
        heatmap_container = ft.Column(expand=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        
        month_dropdown = ft.Dropdown(
            label="Month",
            options=[ft.dropdown.Option(f"{i:02d}") for i in range(1, 13)],
            value=self.current_month, width=125
        )
        year_dropdown = ft.Dropdown(
            label="Year",
            options=[ft.dropdown.Option(str(y)) for y in range(2024, 2031)],
            value=self.current_year, width=125
        )

        def update_heatmap(e=None):
            heatmap_container.controls.clear()
            data = self.tasks_service.list_finalized_tasks(month_dropdown.value, year_dropdown.value)
            
            # Map completion_time to day
            day_map = {}
            for t in data:
                try:
                    day = int(t[5].split("-")[2][:2])
                    day_map[day] = day_map.get(day, []) + [t]
                except (IndexError, ValueError):
                    continue

            grid = ft.GridView(expand=True, runs_count=7, max_extent=50, child_aspect_ratio=1.0, spacing=5, run_spacing=5)
            
            for day in range(1, 32):
                tasks_today = day_map.get(day, [])
                count = len(tasks_today)
                color = self._get_heatmap_color(count)

                def on_day_click(e, ts=tasks_today, d=day):
                    content = ft.ListView(expand=True, spacing=10, height=300)
                    if ts:
                        for t in ts:
                            status_color = ft.Colors.GREEN_ACCENT if t[4] == "Completed" else ft.Colors.RED_ACCENT
                            content.controls.append(
                                ft.ListTile(
                                    title=ft.Text(f"{t[1]} ({t[4]})", color=status_color, weight=ft.FontWeight.BOLD), 
                                    subtitle=ft.Text(f"Deadline: {t[3][:10]} | Earned: {t[6]}"),
                                    bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.BLUE_400)
                                )
                            )
                    else:
                        content.controls.append(ft.Text("No tasks finalized on this day.", italic=True))

                    dialog = ft.AlertDialog(
                        title=ft.Text(f"Tasks: {year_dropdown.value}-{month_dropdown.value}-{d:02d}"), 
                        content=ft.Container(content=content, width=400),
                        actions=[ft.TextButton("Close", on_click=lambda e: self.page.pop_dialog())]
                    )
                    self.page.show_dialog(dialog)

                grid.controls.append(
                    ft.Container(
                        content=ft.Text(str(day), size=10),
                        bgcolor=color, border_radius=3, alignment=ft.Alignment.CENTER,
                        on_click=on_day_click
                    )
                )
            heatmap_container.controls.append(grid)
            self.page.update()

        update_heatmap()

        return ft.Column([
            ft.Container(
                content=ft.Row([
                    ft.Column([
                        ft.Text("Task Name", size=14, weight=ft.FontWeight.W_500, color=ft.Colors.BLUE_200),
                        task_name_input
                    ], expand=True),
                    ft.Column([
                        ft.Text("Deadline", size=14, weight=ft.FontWeight.W_500, color=ft.Colors.BLUE_200),
                        date_btn
                    ]),
                    ft.Column([
                        ft.Text("", size=14),
                        add_btn
                    ])
                ], spacing=20, vertical_alignment=ft.CrossAxisAlignment.END),
                padding=20
            ),
            ft.Row([
                ft.Container(
                    content=ft.Column([ft.Text("Running Tasks", size=18, weight=ft.FontWeight.BOLD), tasks_list], expand=True),
                    expand=1, border=ft.Border.all(1, ft.Colors.GREY_800), border_radius=10, padding=15
                ),
                ft.Container(
                    content=ft.Column([
                        ft.Text("Heatmap", size=18, weight=ft.FontWeight.BOLD),
                        ft.Row([month_dropdown, year_dropdown, ft.IconButton(ft.Icons.REFRESH, on_click=update_heatmap)]),
                        heatmap_container
                    ], expand=True),
                    expand=1, border=ft.Border.all(1, ft.Colors.GREY_800), border_radius=10, padding=15
                )
            ], expand=True)
        ], expand=True, spacing=10)

    def _get_heatmap_color(self, count):
        if count == 0: return ft.Colors.GREY_900
        if count < 2: return ft.Colors.BLUE_200
        if count < 4: return ft.Colors.BLUE_400
        return ft.Colors.BLUE_700

    def _overview_tab(self):
        """
        Builds the Overview tab UI.

        Takes: None
        Gives: ft.Column
        """
        data = self.stats_service.give_overview()

        metrics_row = ft.Row(
            [
                ft.Column([ft.Icon(ft.Icons.LOCAL_FIRE_DEPARTMENT, color=ft.Colors.ORANGE), ft.Text(f"Streak: {data['streak']}", weight=ft.FontWeight.BOLD)], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Column([ft.Icon(ft.Icons.CLOSE, color=ft.Colors.CYAN), ft.Text(f"Multiplier: {data['multiplier']}x", weight=ft.FontWeight.BOLD)], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            ],
            alignment=ft.MainAxisAlignment.CENTER, spacing=40
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

        # 1. Consistency Trend (Line Chart)
        fig1, ax1 = plt.subplots(figsize=(7, 4))
        ax1.set_facecolor(bg_color)
        ax1.plot(data['consistency_trend'], color="#42A5F5", marker="o", linewidth=2)
        ax1.set_title("Consistency Trend (Last 30 Days)", color="white")
        chart1_base64 = fig_to_base64(fig1)

        # 2. Lead Time vs Urgency (Scatter Plot)
        fig2, ax2 = plt.subplots(figsize=(7, 4))
        ax2.set_facecolor(bg_color)
        if data['scatter_points']:
            x, y = zip(*data['scatter_points'])
            ax2.scatter(x, y, color="#FFCA28", alpha=0.6)
            max_val = max(max(x), max(y))
            ax2.plot([0, max_val], [0, max_val], color="red", linestyle="--", alpha=0.5)
        else:
            ax2.text(0.5, 0.5, "No Data", ha='center', va='center')
        ax2.set_xlabel("Vastness (Hours)")
        ax2.set_ylabel("Speed to Finish (Hours)")
        chart2_base64 = fig_to_base64(fig2)

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

        return ft.Column([
            ft.Container(content=metrics_row, padding=20),
            ft.Divider(height=1, color=ft.Colors.GREY_800),
            row_builder(
                "Consistency Trend", 
                ft.Image(src=chart1_base64, height=300, fit=ft.BoxFit.CONTAIN), 
                "This chart shows your task completion volume over the last 30 days. It helps identify if you're a steady worker or a rollercoaster performer.", 
                f"Your completion stability (Standard Deviation) is {data['consistency_std']}."
            ),
            row_builder(
                "Lead Time vs Urgency", 
                ft.Image(src=chart2_base64, height=300, fit=ft.BoxFit.CONTAIN), 
                "X-axis represents 'Broadness' (deadline window), Y-axis is 'Speed to Finish'. Dots near the red line are last-minute completions. Proactive finishes stay far below the line.", 
                "Try to keep your data points in the 'Proactive Zone' far below the diagonal line."
            )
        ], expand=True, scroll=ft.ScrollMode.AUTO, spacing=40)

    def _settings_tab(self):
        """
        Builds the Settings tab UI.

        Takes: None
        Gives: ft.Container
        """
        config = self.settings_service.read_config()
        
        limit_input = ft.TextField(value=str(config["max_tasks"]), label="Running Task Limit", width=200)

        def save_settings(e):
            try:
                self.settings_service.change_max_tasks(int(limit_input.value))
                snack = ft.SnackBar(ft.Text("Settings saved!"))
                self.page.overlay.append(snack)
                snack.open = True
            except ValueError:
                snack = ft.SnackBar(ft.Text("Invalid input. Please enter numbers."))
                self.page.overlay.append(snack)
                snack.open = True
            self.page.update()

        return ft.Container(
            content=ft.Column([
                ft.Text("Todo Configuration", size=18, weight=ft.FontWeight.BOLD),
                limit_input,
                ft.Button("Save Settings", on_click=save_settings, height=50)
            ], spacing=20),
            padding=30, alignment=ft.Alignment.TOP_LEFT
        )
