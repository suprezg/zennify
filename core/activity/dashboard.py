"""
File Name: dashboard.py
Purpose: User interface for the Activity Tracker feature.
"""

import datetime
import flet as ft
import flet_charts as fch
from core.activity.service import ActivitySettings, ActivityStatistics, ActivityReview
from core.shared.configurator import ConfigManager


class ActivityDashboard:
    """
    Main dashboard class for the Activity feature.
    """

    def __init__(self, page):
        """
        Initializes the dashboard with the Flet page.

        Takes: page (ft.Page)
        Gives: None
        """
        self.page = page
        self.settings_service = ActivitySettings()
        self.config_manager = ConfigManager()
        self.stats_service = ActivityStatistics()
        self.review_service = ActivityReview()

        self.current_month = datetime.datetime.now().strftime("%m")
        self.current_year = datetime.datetime.now().strftime("%Y")

    def view(self):
        """
        Builds and displays the main view for the activity dashboard.

        Takes: None
        Gives: None
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

    def _review_tab(self):
        """
        Builds the Review tab UI.

        Takes: None
        Gives: ft.Column
        """
        month_dropdown = ft.Dropdown(
            label="Month",
            options=[ft.dropdown.Option(f"{i:02d}") for i in range(1, 13)],
            value=self.current_month,
            width=120
        )
        year_dropdown = ft.Dropdown(
            label="Year",
            options=[ft.dropdown.Option(str(y)) for y in range(2024, 2031)],
            value=self.current_year,
            width=120
        )

        heatmap_container = ft.Column(visible=False, expand=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        spacer_top = ft.Container(expand=True)
        spacer_bottom = ft.Container(expand=True)

        def show_heatmap(e):
            spacer_top.visible = False
            spacer_bottom.visible = False

            heatmap_container.controls.clear()
            data = self.review_service.get_heatmap(month_dropdown.value, year_dropdown.value)

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
                color = self._get_heatmap_color(freq)

                def on_day_click(e, d=day):
                    self._show_day_details(f"{year_dropdown.value}-{month_dropdown.value}-{d:02d}")

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

        show_button = ft.ElevatedButton("Show", on_click=show_heatmap, height=50)

        controls_row = ft.Row(
            [ft.Text("Select Period:", size=16), month_dropdown, year_dropdown, show_button],
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

    def _get_heatmap_color(self, frequency):
        """
        Returns a blue shade based on activity frequency.

        Takes: frequency (int)
        Gives: str (color) or None
        """
        if frequency == 0: return None
        if frequency < 3: return ft.Colors.BLUE_200
        if frequency < 5: return ft.Colors.BLUE_400
        if frequency < 7: return ft.Colors.BLUE_600
        return ft.Colors.BLUE_900

    def _show_day_details(self, date_str):
        """
        Opens a dialog showing activity details for a specific day.

        Takes: date_str (str)
        Gives: None
        """
        entries = self.review_service.get_activity(date_str)
        content_list = ft.ListView(expand=True, spacing=10, height=400)

        for entry in entries:
            content_list.controls.append(
                ft.Card(
                    content=ft.Container(
                        content=ft.Row(
                            [
                                ft.Text(f"{entry[2]} - {entry[3]}", weight=ft.FontWeight.W_600),
                                ft.Text(f"#{entry[5]}", color=ft.Colors.BLUE_200),
                                ft.Text(f"{entry[7]} coins", color=ft.Colors.GREEN_ACCENT if entry[7] >= 0 else ft.Colors.RED_ACCENT, weight=ft.FontWeight.BOLD)
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                        ),
                        padding=15
                    )
                )
            )

        if not entries:
            content_list.controls.append(ft.Text("No activities logged for this day.", italic=True))

        dialog = ft.AlertDialog(
            title=ft.Text(f"Review: {date_str}"),
            content=ft.Container(content=content_list, width=500),
            actions=[ft.TextButton("Close", on_click=lambda e: self.page.pop_dialog())]
        )
        self.page.show_dialog(dialog)

    def _overview_tab(self):
        """
        Builds the Overview tab UI.

        Takes: None
        Gives: ft.Column
        """
        streak = self.config_manager.read_value("activity", "streak") or 0
        multiplier = self.config_manager.read_value("activity", "multiplier") or 1.0

        metrics_row = ft.Row(
            [
                ft.Row([ft.Icon(ft.Icons.LOCAL_FIRE_DEPARTMENT, color=ft.Colors.ORANGE), ft.Text(f"Streak: {streak}", size=18, weight=ft.FontWeight.BOLD)]),
                ft.Row([ft.Icon(ft.Icons.CLOSE, color=ft.Colors.CYAN), ft.Text(f"Multiplier: {multiplier}x", size=18, weight=ft.FontWeight.BOLD)])
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=50
        )

        month_dropdown = ft.Dropdown(
            label="Month",
            options=[ft.dropdown.Option(f"{i:02d}") for i in range(1, 13)],
            value=self.current_month,
            width=120
        )
        year_dropdown = ft.Dropdown(
            label="Year",
            options=[ft.dropdown.Option(str(y)) for y in range(2024, 2031)],
            value=self.current_year,
            width=120
        )

        charts_container = ft.Column(visible=False, expand=True, scroll=ft.ScrollMode.ALWAYS)
        spacer_mid = ft.Container(expand=True)
        spacer_bottom = ft.Container(expand=True)

        def show_overview(e):
            spacer_mid.visible = False
            spacer_bottom.visible = False
            charts_container.controls.clear()

            data = self.stats_service.give_overview(month_dropdown.value, year_dropdown.value)

            pie_data = data.get("pie_data", {})
            total = pie_data.get("productive", 0) + pie_data.get("unproductive", 0)
            if total > 0:
                prod_per = (pie_data["productive"] / total) * 100
                unprod_per = (pie_data["unproductive"] / total) * 100
                pie_chart = fch.PieChart(
                    sections=[
                        fch.PieChartSection(pie_data["productive"], title=f"{prod_per:.0f}%", color=ft.Colors.GREEN, radius=60, title_style=ft.TextStyle(size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)),
                        fch.PieChartSection(pie_data["unproductive"], title=f"{unprod_per:.0f}%", color=ft.Colors.RED, radius=60, title_style=ft.TextStyle(size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)),
                    ],
                    sections_space=2,
                    center_space_radius=30,
                    expand=True,
                )
            else:
                pie_chart = ft.Container(content=ft.Text("No data", color=ft.Colors.GREY_500), alignment=ft.Alignment.CENTER, expand=True)

            radar_data = data.get("radar_data", [])
            if len(radar_data) >= 3:
                radar_chart = fch.RadarChart(
                    expand=True,
                    titles=[fch.RadarChartTitle(text=item[0]) for item in radar_data],
                    tick_count=3,
                    ticks_text_style=ft.TextStyle(size=12, color=ft.Colors.GREY_400),
                    title_text_style=ft.TextStyle(size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_200),
                    radar_shape=fch.RadarShape.POLYGON,
                    title_position_percentage_offset=0.05,
                    data_sets=[
                        fch.RadarDataSet(
                            fill_color=ft.Colors.with_opacity(0.3, ft.Colors.BLUE_ACCENT),
                            border_color=ft.Colors.BLUE_ACCENT,
                            border_width=2,
                            entry_radius=3,
                            entries=[fch.RadarDataSetEntry(value=item[1]) for item in radar_data],
                        ),
                    ],
                )
            else:
                if 0 < len(radar_data) < 3:
                    dialog = ft.AlertDialog(
                        title=ft.Text("Insufficient Data"),
                        content=ft.Text("Radar chart requires at least 3 unique activities to render."),
                        actions=[ft.TextButton("Close", on_click=lambda e: self.page.pop_dialog())]
                    )
                    self.page.show_dialog(dialog)
                radar_chart = ft.Container(content=ft.Text("Not enough data", color=ft.Colors.GREY_500), alignment=ft.Alignment.CENTER, expand=True)

            bar_data = data.get("bar_data", [])
            if bar_data:
                bar_groups = []
                axis_labels = []
                for i, (tag, count) in enumerate(bar_data):
                    bar_groups.append(
                        fch.BarChartGroup(
                            x=i,
                            rods=[fch.BarChartRod(from_y=0, to_y=count, color=ft.Colors.CYAN_700, width=30, border_radius=3)]
                        )
                    )
                    axis_labels.append(fch.ChartAxisLabel(value=i, label=ft.Text(tag, size=12, color=ft.Colors.GREY_400, no_wrap=True)))
                
                max_count = max(item[1] for item in bar_data) if bar_data else 10
                bar_chart = fch.BarChart(
                    groups=bar_groups,
                    interactive=True,
                    bottom_axis=fch.ChartAxis(labels=axis_labels, label_size=30),
                    left_axis=fch.ChartAxis(labels=[fch.ChartAxisLabel(value=0, label=ft.Text("0", size=10)), fch.ChartAxisLabel(value=max_count, label=ft.Text(str(max_count), size=10))], label_size=30),
                    expand=True,
                )
            else:
                bar_chart = ft.Container(content=ft.Text("No data", color=ft.Colors.GREY_500), alignment=ft.Alignment.CENTER, expand=True)

            row1 = ft.Row(
                [
                    ft.Container(content=ft.Column([ft.Text("Activity Mix (Top 5)", size=14, weight=ft.FontWeight.BOLD), radar_chart], horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True), bgcolor=None, expand=True, height=300, border_radius=10, padding=15, margin=5, border=ft.Border.all(2, ft.Colors.WHITE)),
                    ft.Container(content=ft.Column([ft.Text("Productivity Ratio", size=14, weight=ft.FontWeight.BOLD), pie_chart], horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True), bgcolor=None, expand=True, height=300, border_radius=10, padding=15, margin=5, border=ft.Border.all(2, ft.Colors.WHITE)),
                ]
            )
            row2 = ft.Row(
                [
                    ft.Container(content=ft.Column([ft.Text("Detailed Tag Frequency", size=14, weight=ft.FontWeight.BOLD), bar_chart], horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True), bgcolor=None, expand=True, height=350, border_radius=10, padding=15, margin=5, border=ft.Border.all(2, ft.Colors.WHITE))
                ]
            )

            charts_container.controls.extend([row1, row2])
            charts_container.visible = True
            self.page.update()

        show_button = ft.ElevatedButton("Show", on_click=show_overview, height=50)

        picker_row = ft.Row(
            [ft.Text("Filter:", size=16), month_dropdown, year_dropdown, show_button],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=20
        )

        return ft.Column(
            [
                ft.Container(content=metrics_row, padding=30),
                spacer_mid,
                ft.Container(content=picker_row),
                charts_container,
                spacer_bottom
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            expand=True
        )

    def _settings_tab(self):
        """
        Builds the Settings tab UI.

        Takes: None
        Gives: ft.Container
        """
        service_status = self.config_manager.read_value("activity", "service_status") or False
        popup_interval = self.config_manager.read_value("activity", "popup_interval_timer") or "30m"
        popup_visible = self.config_manager.read_value("activity", "popup_visible_timer") or "1m"

        def update_service(e):
            self.settings_service.toggle_service(e.control.value)

        def update_interval(e):
            self.settings_service.change_popup_interval_timer(e.control.value)

        def update_visible(e):
            self.settings_service.change_popup_visible_timer(e.control.value)

        return ft.Container(
            content=ft.Column(
                [
                    ft.Container(
                        content=ft.Row(
                            [
                                ft.Text("Background Service", size=18),
                                ft.Switch(value=service_status, on_change=update_service)
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
                                    on_select=update_interval
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
                                    on_select=update_visible
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
