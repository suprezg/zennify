"""
File Name: dashboard.py
Purpose: User interface for the Activity Tracker feature.
"""

import datetime
import flet as ft
from core.activity.service import ActivitySettings, ActivityStatistics, ActivityReview
from core.shared.wallet import WalletManager


class ActivityDashboard:
    """
    Main dashboard class for the Activity feature.
    Handles UI rendering and interaction for activity tracking, overview, and settings.
    """

    def __init__(self, page):
        """
        Initializes the dashboard with the Flet page and necessary services.

        Takes:
            page (ft.Page): The root page object for rendering the dashboard.

        Gives:
            None: Initializes service instances and current date attributes.
        """
        self.page = page
        self.settings_service = ActivitySettings()
        self.stats_service = ActivityStatistics()
        self.review_service = ActivityReview()

        self.current_month = datetime.datetime.now().strftime("%m")
        self.current_year = datetime.datetime.now().strftime("%Y")

    def view(self):
        """
        Builds and displays the main view for the activity dashboard.

        Takes:
            None: Operates on the internal 'page' attribute.

        Gives:
            None: Cleans the page and adds the tabs container.
        """
        self.page.title = "Zennify - Activity Tracker"
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.window.min_width = 800
        self.page.window.min_height = 600
        self.page.clean()

        tabs = ft.Tabs(
            length=3,
            selected_index=0,
            animation_duration=300,
            expand=True,
            content=ft.Column(
                expand=True,
                controls=[
                    ft.TabBar(
                        tabs=[
                            ft.Tab(label="Review"),
                            ft.Tab(label="Overview"),
                            ft.Tab(label="Settings"),
                        ]
                    ),
                    ft.TabBarView(
                        expand=True,
                        controls=[
                            self._review_tab(),
                            self._overview_tab(),
                            self._settings_tab(),
                        ],
                    ),
                ],
            ),
        )

        self.page.add(tabs)

        if WalletManager().is_bankrupt() == -1:
            dialog = ft.AlertDialog(
                title=ft.Text("Wallet Warning"),
                content=ft.Text("Your wallet balance is currently negative. You can try to recover by being more productive or declare bankruptcy by running 'zennify.sh --bankrupt' in your terminal."),
                actions=[ft.TextButton("Close", on_click=lambda e: self.page.pop_dialog())]
            )
            self.page.show_dialog(dialog)

    def _review_tab(self):
        """
        Builds the Review tab UI, including the activity heatmap.

        Takes:
            None: Uses internal services and attributes.

        Gives:
            ft.Column: A scrollable column containing the period selector and heatmap.
        """
        period_input = ft.TextField(
            label="Period (mm/yyyy)",
            value=f"{self.current_month}/{self.current_year}",
            hint_text="05/2026",
            width=180,
            text_align=ft.TextAlign.CENTER
        )

        heatmap_container = ft.Column(visible=False, expand=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        spacer_top = ft.Container(expand=True)
        spacer_bottom = ft.Container(expand=True)

        def get_heatmap_color(frequency):
            """
            Returns a blue shade based on activity frequency.

            Takes:
                frequency (int): The number of activities logged for a day.

            Gives:
                str: A Flet color constant or None if frequency is 0.
            """
            if frequency == 0: return None
            if frequency < 3: return ft.Colors.BLUE_200
            if frequency < 5: return ft.Colors.BLUE_400
            if frequency < 7: return ft.Colors.BLUE_600
            return ft.Colors.BLUE_900

        def show_day_details(date_str):
            """
            Opens a dialog showing activity details for a specific day.

            Takes:
                date_str (str): The date in 'yyyy-mm-dd' format.

            Gives:
                None: Displays an AlertDialog on the page.
            """
            entries = self.review_service.get_activity(date_str)
            content_list = ft.ListView(expand=True, spacing=10, height=300)

            for entry in entries:
                status = "Productive" if entry[6] else "Unproductive"
                status_color = ft.Colors.GREEN_ACCENT if entry[6] else ft.Colors.RED_ACCENT
                content_list.controls.append(
                    ft.ListTile(
                        title=ft.Text(f"#{entry[5]} ({status})", color=status_color, weight=ft.FontWeight.BOLD),
                        subtitle=ft.Text(f"{entry[2]} - {entry[3]} | Earned: {entry[7]} coins"),
                        bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.BLUE_400)
                    )
                )

            if not entries:
                content_list.controls.append(ft.Text("No activities logged for this day.", italic=True))

            dialog = ft.AlertDialog(
                title=ft.Text(f"Review: {date_str}"),
                content=ft.Container(content=content_list, width=400),
                actions=[ft.TextButton("Close", on_click=lambda e: self.page.pop_dialog())]
            )
            self.page.show_dialog(dialog)

        def show_heatmap(e):
            """
            Parses the period input and renders the activity heatmap.

            Takes:
                e (ft.ControlEvent): The event object from the 'Show' button click.

            Gives:
                None: Updates the heatmap container and refreshes the page.
            """
            spacer_top.visible = False
            spacer_bottom.visible = False

            try:
                period = period_input.value.strip()
                if "/" not in period:
                    raise ValueError
                month, year = period.split("/")
                if not (month.isdigit() and 1 <= int(month) <= 12 and year.isdigit() and len(year) == 4):
                    raise ValueError
            except ValueError:
                self.page.snack_bar = ft.SnackBar(ft.Text("Please enter period as mm/yyyy (e.g., 05/2026)"))
                self.page.snack_bar.open = True
                self.page.update()
                return

            heatmap_container.controls.clear()
            data = self.review_service.get_heatmap(month, year)

            grid = ft.GridView(
                expand=True,
                runs_count=7,
                max_extent=60,
                child_aspect_ratio=1.0,
                spacing=8,
                run_spacing=8,
            )

            for day in range(1, 32):
                freq = data.get(day, 0)
                color = get_heatmap_color(freq)

                def on_day_click(e, d=day, m=month, y=year):
                    show_day_details(f"{y}-{m}-{d:02d}")

                grid.controls.append(
                    ft.Container(
                        content=ft.Text(str(day), size=12, weight=ft.FontWeight.BOLD),
                        bgcolor=color,
                        border_radius=5,
                        alignment=ft.Alignment.CENTER,
                        on_click=on_day_click,
                        animate=ft.Animation(300, ft.AnimationCurve.EASE_OUT)
                    )
                )

            heatmap_container.controls.append(
                ft.Container(content=grid, padding=20, alignment=ft.Alignment.CENTER)
            )
            heatmap_container.visible = True
            self.page.update()

        show_button = ft.Button("Show", on_click=show_heatmap, height=50)

        controls_row = ft.Row(
            [ft.Text("Select Period:", size=16), period_input, show_button],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=20
        )

        return ft.Column(
            [
                spacer_top,
                ft.Container(content=controls_row, padding=20),
                heatmap_container,
                spacer_bottom
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            expand=True
        )

    def _overview_tab(self):
        """
        Builds the Overview tab UI with metrics and charts.

        Takes:
            None: Uses internal stats service and config manager.

        Gives:
            ft.Column: A scrollable column containing stats and charts.
        """
        streak, multiplier = self.settings_service.get_streak_data()

        metrics_row = ft.Row(
            [
                ft.Row([ft.Icon(ft.Icons.LOCAL_FIRE_DEPARTMENT, color=ft.Colors.ORANGE), ft.Text(f"Streak: {streak}", size=18, weight=ft.FontWeight.BOLD)]),
                ft.Row([ft.Icon(ft.Icons.CLOSE, color=ft.Colors.CYAN), ft.Text(f"Multiplier: {multiplier}x", size=18, weight=ft.FontWeight.BOLD)])
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=50
        )

        period_input = ft.TextField(
            label="Filter (mm/yyyy)",
            value=f"{self.current_month}/{self.current_year}",
            hint_text="05/2026",
            width=180,
            text_align=ft.TextAlign.CENTER
        )

        charts_container = ft.Column(visible=False, expand=True, spacing=40)
        spacer_mid = ft.Container(expand=True)
        spacer_bottom = ft.Container(expand=True)

        def row_builder(title, visual_content, explanation, insight):
            """
            Helper to build a standardized layout for metrics.

            Takes:
                title (str): Metric title.
                visual_content (ft.Control): The chart or visual representation.
                explanation (str): Technical explanation of the metric.
                insight (str): Personalized insight derived from the data.

            Gives:
                ft.Row: A formatted row containing visual and text components.
            """
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

        def show_overview(e):
            """
            Generates and displays overview charts for the selected period.

            Takes:
                e (ft.ControlEvent): The event object from the 'Show' button click.

            Gives:
                None: Updates charts_container and refreshes the page.
            """
            spacer_mid.visible = False
            spacer_bottom.visible = False

            try:
                period = period_input.value.strip()
                if "/" not in period:
                    raise ValueError
                month, year = period.split("/")
                if not (month.isdigit() and 1 <= int(month) <= 12 and year.isdigit() and len(year) == 4):
                    raise ValueError
            except ValueError:
                self.page.snack_bar = ft.SnackBar(ft.Text("Please enter period as mm/yyyy (e.g., 05/2026)"))
                self.page.snack_bar.open = True
                self.page.update()
                return

            charts_container.controls.clear()
            overview_data = self.stats_service.give_overview(month, year)

            rows = []
            for item in overview_data:
                rows.append(
                    row_builder(
                        item["title"],
                        ft.Image(src=item["image_base64"], height=300, fit=ft.BoxFit.CONTAIN),
                        item["explanation"],
                        item["insight"]
                    )
                )

            charts_container.controls.extend(rows)
            charts_container.visible = True
            self.page.update()
            return

        show_button = ft.Button("Show", on_click=show_overview, height=50)

        picker_row = ft.Row(
            [ft.Text("Filter:", size=16), period_input, show_button],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=20
        )

        return ft.Column(
            [
                ft.Container(content=metrics_row, padding=20),
                ft.Divider(height=1, color=ft.Colors.GREY_800),
                spacer_mid,
                ft.Container(content=picker_row, padding=20),
                ft.Divider(height=1, color=ft.Colors.TRANSPARENT),
                charts_container,
                spacer_bottom
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            spacing=30
        )

    def _settings_tab(self):
        """
        Builds the Settings tab UI for activity configuration.

        Takes:
            None: Uses internal config manager and settings service.

        Gives:
            ft.Container: A centered container with activity settings.
        """
        service_status = self.settings_service.get_service_details()[-1]
        popup_interval, popup_visible= self.settings_service.get_timer_details()

        return ft.Container(
            content=ft.Column(
                [
                    ft.Container(
                        content=ft.Row(
                            [
                                ft.Text("Background Service", size=18),
                                ft.Switch(value=service_status, on_change=lambda e: self.settings_service.toggle_service(e.control.value))
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                        ),
                        width=500
                    ),
                    ft.Container(
                        content=ft.Row(
                            [
                                ft.Text("Popup Interval", size=18),
                                ft.Dropdown(
                                    options=[ft.dropdown.Option(o) for o in ["30m", "1h", "2h", "3h"]],
                                    value=popup_interval,
                                    width=200,
                                    on_select=lambda e: self.settings_service.change_popup_interval_timer(e.control.value)
                                )
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                        ),
                        width=500
                    ),
                    ft.Container(
                        content=ft.Row(
                            [
                                ft.Text("Minimum Visible Time", size=18),
                                ft.Dropdown(
                                    options=[ft.dropdown.Option(o) for o in ["2m", "5m", "10m", "15m"]],
                                    value=popup_visible,
                                    width=200,
                                    on_select=lambda e: self.settings_service.change_popup_visible_timer(e.control.value)
                                )
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                        ),
                        width=500
                    ),
                ],
                spacing=30,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER
            ),
            padding=50,
            alignment=ft.Alignment.TOP_CENTER
        )
