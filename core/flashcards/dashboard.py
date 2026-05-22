"""
File Name: dashboard.py
Purpose: User interface for the Flashcards feature with centered layout and list tiles.
"""

import os
import flet as ft
import flet_charts as fch
import datetime
from core.flashcards.service import FlashcardRevision, FlashcardSettings, FlashcardStorage, FlashcardStatistics
from core.shared.configurator import ConfigManager


class FlashcardDashboard:
    """
    Main dashboard class for the Flashcard feature.
    """

    def __init__(self, page):
        """
        Initializes the dashboard with the Flet page.

        Takes: page (ft.Page)
        Gives: None
        """
        self.page = page
        self.revision_service = FlashcardRevision()
        self.settings_service = FlashcardSettings()
        self.storage_service = FlashcardStorage()
        self.stats_service = FlashcardStatistics()
        self.config_manager = ConfigManager()

    def view(self, selected_index=0):
        """
        Builds and displays the main view for the flashcard dashboard.

        Takes: selected_index (int)
        Gives: None
        """
        self.revision_service.scan_folder()
        self.page.title = "Zennify - Flashcards"
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
                            ft.Tab(label="Revision"),
                            ft.Tab(label="Overview"),
                            ft.Tab(label="Settings"),
                        ]
                    ),
                    ft.TabBarView(
                        expand=True,
                        controls=[
                            self._revision_tab(),
                            self._overview_tab(),
                            self._settings_tab(),
                        ],
                    ),
                ],
            ),
        )
        self.page.add(tabs)

    def _overview_tab(self):
        """
        Builds the Overview tab UI with charts and metrics.

        Takes: None
        Gives: ft.Column
        """
        data = self.stats_service.give_overview()
        g_stats = data["global"]
        d_stats = data["deck"]

        # Check for minimum revision threshold (e.g., 5 cards)
        if g_stats["revised_count"] < 5:
            return ft.Column([
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.ANALYTICS_OUTLINED, size=50, color=ft.Colors.GREY_400),
                        ft.Text("Not Enough Data", size=24, weight=ft.FontWeight.BOLD),
                        ft.Text(f"Revise at least 5 cards to see your analytics. ({g_stats['revised_count']}/5)", color=ft.Colors.GREY_400),
                        ft.ElevatedButton("Go to Revision", on_click=lambda _: self.view(0), height=50)
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    expand=True,
                    alignment=ft.Alignment.CENTER
                )
            ], expand=True)

        # 1. Top Metrics (Activity Style)
        streak = g_stats["streak"]
        multiplier = g_stats["multiplier"]
        metrics_row = ft.Row(
            [
                ft.Row([ft.Icon(ft.Icons.LOCAL_FIRE_DEPARTMENT, color=ft.Colors.ORANGE), ft.Text(f"Streak: {streak}", size=18, weight=ft.FontWeight.BOLD)]),
                ft.Row([ft.Icon(ft.Icons.CLOSE, color=ft.Colors.CYAN), ft.Text(f"Multiplier: {multiplier}x", size=18, weight=ft.FontWeight.BOLD)])
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=50
        )

        # 2. Middle Row Metrics
        mid_metrics = ft.Row([
            ft.Column([ft.Text("Active Knowledge", size=12, color=ft.Colors.GREY_400), ft.Text(f"{g_stats['active_knowledge']}%", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_ACCENT)], horizontal_alignment="center"),
            ft.Column([ft.Text("Success Rate", size=12, color=ft.Colors.GREY_400), ft.Text(f"{d_stats['success_rate']}%", size=24, weight=ft.FontWeight.BOLD)], horizontal_alignment="center"),
            ft.Column([ft.Text("Efficiency", size=12, color=ft.Colors.GREY_400), ft.Text(f"{d_stats['efficiency']} d/rev", size=24, weight=ft.FontWeight.BOLD)], horizontal_alignment="center"),
        ], alignment=ft.MainAxisAlignment.CENTER, spacing=100)

        # 3. Charts Preparation
        
        # Ease Factor Distribution (Bar)
        diff_groups = [
            fch.BarChartGroup(x=i, rods=[fch.BarChartRod(from_y=0, to_y=count, color=ft.Colors.BLUE_400, width=40)])
            for i, (_, count) in enumerate(g_stats["difficulty_dist"])
        ]
        diff_labels = [fch.ChartAxisLabel(value=i, label=ft.Text(label, size=10)) for i, (label, _) in enumerate(g_stats["difficulty_dist"])]
        diff_chart = fch.BarChart(
            groups=diff_groups, bottom_axis=fch.ChartAxis(labels=diff_labels, label_size=30),
            expand=True, interactive=True
        )

        # Memory Stability (Bar)
        stab_groups = [
            fch.BarChartGroup(x=i, rods=[fch.BarChartRod(from_y=0, to_y=count, color=ft.Colors.CYAN_400, width=40)])
            for i, (_, count) in enumerate(d_stats["stability"])
        ]
        stab_labels = [fch.ChartAxisLabel(value=i, label=ft.Text(label, size=10)) for i, (label, _) in enumerate(d_stats["stability"])]
        stab_chart = fch.BarChart(groups=stab_groups, bottom_axis=fch.ChartAxis(labels=stab_labels, label_size=30), expand=True)

        # Review Forecast (Line) - Increased X labels
        forecast_points = [fch.LineChartDataPoint(i, count) for i, (_, count) in enumerate(g_stats["forecast"])]
        forecast_chart = fch.LineChart(
            data_series=[fch.LineChartData(points=forecast_points, color=ft.Colors.AMBER, stroke_width=3, curved=True)],
            expand=True, interactive=True,
            bottom_axis=fch.ChartAxis(labels=[fch.ChartAxisLabel(value=i, label=ft.Text(g_stats["forecast"][i][0][-5:], size=10)) for i in range(0, 30, 2)], label_size=30)
        )

        # 4. Layout
        return ft.Column([
            ft.Container(content=metrics_row, padding=20),
            ft.Container(content=mid_metrics, padding=10),
            ft.Divider(height=1, color=ft.Colors.GREY_800),
            # Row 1: Ease Factor & Stability
            ft.Row([
                ft.Container(
                    content=ft.Column([
                        ft.Text("Ease Factor Distribution", weight=ft.FontWeight.BOLD),
                        ft.Container(content=diff_chart)
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    expand=True, height=300, border=ft.Border.all(2, ft.Colors.WHITE), border_radius=10, margin=5
                ),
                ft.Container(
                    content=ft.Column([
                        ft.Text("Memory Stability (Strength)", weight=ft.FontWeight.BOLD),
                        ft.Container(content=stab_chart)
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    expand=True, height=300, border=ft.Border.all(2, ft.Colors.WHITE), border_radius=10, margin=5
                ),
            ]),
            # Row 2: Line Chart
            ft.Container(
                content=ft.Column([
                    ft.Text("30-Day Review Forecast", weight=ft.FontWeight.BOLD),
                    ft.Container(content=forecast_chart)
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                expand=True, height=350, border=ft.Border.all(2, ft.Colors.WHITE), border_radius=10, margin=5
                )
            ], expand=True, scroll=ft.ScrollMode.AUTO, spacing=20)

    def _revision_tab(self):
        """
        Builds the Revision tab UI with a centered list of decks.

        Takes: None
        Gives: ft.Column
        """
        def get_deck_stats():
            """
            Retrieves counts of pending cards per deck.

            Takes: None
            Gives: tuple
            """
            now = datetime.datetime.now(datetime.timezone.utc).isoformat()
            cards = self.storage_service.read_entries("SELECT deck_name FROM flashcard WHERE next_review <= ?", (now,))
            deck_counts = {}
            for card in cards:
                deck = card[0]
                deck_counts[deck] = deck_counts.get(deck, 0) + 1
            return deck_counts, len(cards)

        deck_counts, total_pending = get_deck_stats()
        
        decks_list = ft.ListView(expand=True, spacing=5)
        
        def update_decks_list():
            """
            Refreshes the decks list UI with current statistics.

            Takes: None
            Gives: None
            """
            decks_list.controls.clear()
            decks_list.controls.append(
                ft.ListTile(
                    leading=ft.Icon(ft.Icons.ALL_INBOX, color=ft.Colors.BLUE_400),
                    title=ft.Text("ALL DECKS", weight=ft.FontWeight.BOLD),
                    trailing=ft.Text(str(total_pending), size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_400),
                    bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.BLUE_900),
                )
            )
            for deck, count in sorted(deck_counts.items()):
                decks_list.controls.append(
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.FOLDER_OPEN, color=ft.Colors.AMBER_400),
                        title=ft.Text(deck),
                        trailing=ft.Text(str(count), size=14, color=ft.Colors.AMBER_400),
                    )
                )

        update_decks_list()
            
        deck_dropdown = ft.Dropdown(
            label="Select Deck for Revision",
            options=[ft.dropdown.Option("ALL")] + [ft.dropdown.Option(d) for d in sorted(deck_counts.keys())],
            value="ALL",
            width=300
        )

        def on_rescan(e):
            """
            Handles the rescan button click event.

            Takes: e (ControlEvent)
            Gives: None
            """
            self.revision_service.scan_folder()
            nonlocal deck_counts, total_pending
            deck_counts, total_pending = get_deck_stats()
            update_decks_list()
            deck_dropdown.options = [ft.dropdown.Option("ALL")] + [ft.dropdown.Option(d) for d in sorted(deck_counts.keys())]
            deck_dropdown.value = "ALL"
            self.page.update()

        def on_revise(e):
            """
            Handles the revise button click event.

            Takes: e (ControlEvent)
            Gives: None
            """
            deck = deck_dropdown.value
            cards = self.revision_service.revise_deck(deck)
            if not cards:
                dialog = ft.AlertDialog(title=ft.Text("No pending cards"), content=ft.Text("You are all caught up for this deck!"))
                self.page.show_dialog(dialog)
                return
                
            self._start_fsrs_session(cards)

        rescan_btn = ft.IconButton(icon=ft.Icons.SYNC, on_click=on_rescan, tooltip="Rescan Folder")
        revise_btn = ft.ElevatedButton("Start Revision", on_click=on_revise, height=50)

        return ft.Column([
            ft.Row([rescan_btn], alignment=ft.MainAxisAlignment.END),
            ft.Container(
                content=ft.Column([
                    ft.Container(
                        content=decks_list,
                        width=500,
                        height=350,
                        border=ft.Border.all(1, ft.Colors.GREY_800),
                        border_radius=10,
                        padding=10
                    ),
                    ft.Container(height=20),
                    ft.Row([deck_dropdown, revise_btn], alignment=ft.MainAxisAlignment.CENTER, spacing=30)
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                expand=True,
                alignment=ft.Alignment.CENTER
            )
        ], expand=True, spacing=30, scroll=ft.ScrollMode.AUTO)

    def _start_fsrs_session(self, cards):
        """
        Starts the revision session with FSRS v6 ratings.

        Takes: cards (list)
        Gives: None
        """
        current_index = 0
        total_cards = len(cards)
        
        card_text = ft.Text(cards[current_index]["question"], size=22, weight=ft.FontWeight.W_500, text_align=ft.TextAlign.CENTER)
        answer_text = ft.Text(cards[current_index]["answer"], size=18, color=ft.Colors.GREY_300, visible=False)
        
        progress_text = ft.Text(f"Card 1 of {total_cards}", size=14, color=ft.Colors.GREY_400)
        
        def show_answer(e):
            """
            Reveals the answer and shows FSRS rating buttons.

            Takes: e (ControlEvent)
            Gives: None
            """
            answer_text.visible = True
            show_btn.visible = False
            rating_row.visible = True
            self.page.update()
            
        def rate_card(e, quality):
            """
            Processes the card rating using FSRS v6 and advances.

            Takes: e (ControlEvent), quality (int)
            Gives: None
            """
            nonlocal current_index
            self.revision_service.schdule_card(cards[current_index]["id"], quality)
            
            current_index += 1
            if current_index >= total_cards:
                self.page.pop_dialog()
                self.view() 
                self.page.update()
                return
                
            card_text.value = cards[current_index]["question"]
            answer_text.value = cards[current_index]["answer"]
            answer_text.visible = False
            progress_text.value = f"Card {current_index + 1} of {total_cards}"
            
            show_btn.visible = True
            rating_row.visible = False
            self.page.update()

        show_btn = ft.ElevatedButton("Show Answer", on_click=show_answer, height=50)
        
        rating_row = ft.Row([
            ft.ElevatedButton("Again", on_click=lambda e: rate_card(e, 1), bgcolor=ft.Colors.RED_700, color=ft.Colors.WHITE),
            ft.ElevatedButton("Hard", on_click=lambda e: rate_card(e, 2), bgcolor=ft.Colors.ORANGE_700, color=ft.Colors.WHITE),
            ft.ElevatedButton("Good", on_click=lambda e: rate_card(e, 3), bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE),
            ft.ElevatedButton("Easy", on_click=lambda e: rate_card(e, 4), bgcolor=ft.Colors.BLUE_700, color=ft.Colors.WHITE)
        ], visible=False, alignment=ft.MainAxisAlignment.CENTER, spacing=15)

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row([ft.Text("Revision Session"), progress_text], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            content=ft.Container(
                content=ft.Column([
                    ft.Container(content=card_text, padding=20, alignment=ft.Alignment.CENTER),
                    ft.Divider(height=1, color=ft.Colors.GREY_800),
                    ft.Container(content=answer_text, padding=20, alignment=ft.Alignment.CENTER, expand=True)
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                width=600, height=400
            ),
            actions=[
                ft.Container(content=show_btn, alignment=ft.Alignment.CENTER),
                rating_row,
                ft.Row([ft.TextButton("Exit Session", on_click=lambda e: self.page.pop_dialog())], alignment=ft.MainAxisAlignment.END)
            ],
            actions_alignment=ft.MainAxisAlignment.CENTER,
            content_padding=10
        )
        self.page.show_dialog(dialog)

    def _settings_tab(self):
        """
        Builds the Settings tab UI.

        Takes: None
        Gives: ft.Container
        """
        current_path = self.config_manager.read_value("flashcard", "folder_path") or ""
        
        path_input = ft.TextField(
            value=current_path,
            expand=True,
            hint_text="e.g., /path/to/your/markdown/notes"
        )
        
        def update_path(e):
            """
            Handles the folder path update action.

            Takes: e (ControlEvent)
            Gives: None
            """
            if not os.path.exists(path_input.value):
                snack = ft.SnackBar(ft.Text("Directory does not exist!"))
                self.page.overlay.append(snack)
                snack.open = True
                self.page.update()
                return
                
            self.settings_service.change_folder(path_input.value)
            self.view(selected_index=2)
            snack = ft.SnackBar(ft.Text("Path updated and folder rescanned!"))
            self.page.overlay.append(snack)
            snack.open = True
            self.page.update()

        update_btn = ft.ElevatedButton("Update & Rescan", on_click=update_path, height=50)

        return ft.Container(
            content=ft.Column([
                ft.Text("Flashcards Root Directory", size=18),
                ft.Text("Specify the root folder where your markdown flashcards are stored.", color=ft.Colors.GREY_400),
                ft.Row([path_input, update_btn], alignment=ft.MainAxisAlignment.START, spacing=20)
            ], scroll=ft.ScrollMode.AUTO),
            padding=30,
            alignment=ft.Alignment.TOP_LEFT
        )
