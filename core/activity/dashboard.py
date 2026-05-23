"""
File Name: dashboard.py
Purpose: User interface for the Activity Tracker feature.
"""

import datetime
import io
import base64
import math
import flet as ft
import matplotlib
import matplotlib.pyplot as plt
from core.activity.service import ActivitySettings, ActivityStatistics, ActivityReview
from core.shared.configurator import ConfigManager

matplotlib.use("agg")


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

        charts_container = ft.Column(visible=False, expand=True, spacing=40)
        spacer_mid = ft.Container(expand=True)
        spacer_bottom = ft.Container(expand=True)

        bg_color = "#111418"
        plt.rcParams.update({
            "text.color": "white",
            "axes.labelcolor": "white",
            "xtick.color": "white",
            "ytick.color": "white",
            "axes.edgecolor": "white",
        })

        def fig_to_base64(fig):
            buf = io.BytesIO()
            fig.tight_layout(pad=1.5)
            fig.savefig(buf, format="png", bbox_inches="tight", facecolor=bg_color, dpi=100)
            plt.close(fig)
            return base64.b64encode(buf.getvalue()).decode("utf-8")

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

        def show_overview(e):
            spacer_mid.visible = False
            spacer_bottom.visible = False
            charts_container.controls.clear()

            data = self.stats_service.give_overview(month_dropdown.value, year_dropdown.value)

            # 1. Productivity Ratio (Pie Chart)
            fig1, ax1 = plt.subplots(figsize=(7, 4))
            ax1.set_facecolor(bg_color)
            pie_data = data.get("pie_data", {})
            prod = pie_data.get("productive", 0)
            unprod = pie_data.get("unproductive", 0)
            total = prod + unprod
            if total > 0:
                ax1.pie([prod, unprod], labels=["Productive", "Unproductive"], autopct='%1.1f%%', colors=["#66BB6A", "#EF5350"], textprops={'color':"w"})
                prod_pc = round((prod / total * 100), 1)
            else:
                ax1.text(0.5, 0.5, "No Data", ha='center', va='center', color="white")
                prod_pc = 0
            chart1_base64 = fig_to_base64(fig1)

            # 2. Activity Mix (Top 5) (Radar Chart)
            radar_data = data.get("radar_data", [])
            fig2 = plt.figure(figsize=(7, 4))
            fig2.patch.set_facecolor(bg_color)
            if len(radar_data) >= 3:
                ax2 = fig2.add_subplot(111, polar=True)
                ax2.set_facecolor(bg_color)
                labels = [item[0] for item in radar_data]
                values = [item[1] for item in radar_data]
                num_vars = len(labels)
                angles = [n / float(num_vars) * 2 * math.pi for n in range(num_vars)]
                angles += angles[:1]
                values += values[:1]
                ax2.plot(angles, values, linewidth=1, linestyle='solid', color="#42A5F5")
                ax2.fill(angles, values, "#42A5F5", alpha=0.3)
                ax2.set_xticks(angles[:-1])
                ax2.set_xticklabels(labels, color="white", size=10)
                ax2.tick_params(axis='y', colors='white')
                top_activity = labels[0] if labels else "None"
            else:
                ax2 = fig2.add_subplot(111)
                ax2.set_facecolor(bg_color)
                ax2.text(0.5, 0.5, "Not enough data (needs 3+)", ha='center', va='center', color="white")
                ax2.axis('off')
                top_activity = "None"
            chart2_base64 = fig_to_base64(fig2)

            # 3. Detailed Tag Frequency (Bar Chart)
            fig3, ax3 = plt.subplots(figsize=(7, 4))
            ax3.set_facecolor(bg_color)
            bar_data = data.get("bar_data", [])
            if bar_data:
                labels = [item[0] for item in bar_data]
                counts = [item[1] for item in bar_data]
                ax3.bar(labels, counts, color="#26C6DA")
                ax3.tick_params(axis='x', rotation=45)
            else:
                ax3.text(0.5, 0.5, "No Data", ha='center', va='center', color="white")
            chart3_base64 = fig_to_base64(fig3)

            rows = [
                row_builder(
                    "Productivity Ratio",
                    ft.Image(src=chart1_base64, height=300, fit=ft.BoxFit.CONTAIN),
                    "This chart shows the balance between your productive and unproductive sessions. It gives a quick glance at how effectively you're spending your logged time.",
                    f"Your productivity ratio for this month is {prod_pc}%."
                ),
                row_builder(
                    "Activity Mix (Top 5)",
                    ft.Image(src=chart2_base64, height=300, fit=ft.BoxFit.CONTAIN),
                    "The radar chart displays your top 5 activities, forming a 'shape' of your habits. A well-rounded shape indicates varied activities, while spikes show intense focus on specific areas.",
                    f"Your dominant activity is '{top_activity}'."
                ),
                row_builder(
                    "Detailed Tag Frequency",
                    ft.Image(src=chart3_base64, height=300, fit=ft.BoxFit.CONTAIN),
                    "This bar chart provides a detailed breakdown of all your activity tags by their frequency of use, highlighting where your time is being invested the most.",
                    f"You have tracked {len(bar_data)} different activities this month."
                )
            ]

            charts_container.controls.extend(rows)
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
                ft.Container(content=metrics_row, padding=20),
                ft.Divider(height=1, color=ft.Colors.GREY_800),
                spacer_mid,
                ft.Container(content=picker_row, padding=20),
                ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
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
