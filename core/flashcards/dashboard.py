"""
File Name: dashboard.py
Purpose: User interface for the Flashcards feature with centered layout and list tiles.
"""

import os
import flet as ft
import datetime
from core.flashcards.service import FlashcardRevision, FlashcardSettings, FlashcardStatistics

class FlashcardDashboard:
    """
    Main dashboard class for the Flashcard feature.
    """

    def __init__(self, page):
        """
        Initializes the dashboard with the Flet page.

        Takes:
            page (ft.Page): The root page object for rendering the dashboard.

        Gives:
            None: Initializes service instances.
        """
        self.page = page
        self.revision_service = FlashcardRevision()
        self.settings_service = FlashcardSettings()
        self.stats_service = FlashcardStatistics()

    def view(self, selected_index=0):
        """
        Builds and displays the main view for the flashcard dashboard.

        Takes:
            selected_index (int): The index of the tab to be selected initially.

        Gives:
            None: Cleans the page and adds the tabs container.
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

    def _revision_tab(self):
        """
        Builds the Revision tab UI with a centered list of decks.

        Takes:
            None: Uses internal services.

        Gives:
            ft.Column: A scrollable column containing the revision UI.
        """

        deck_counts, total_pending = self.revision_service.get_deck_stats()
        
        decks_list = ft.ListView(expand=True, spacing=5)
        
        def update_decks_list():
            """
            Refreshes the decks list UI with current statistics.

            Takes:
                None: Uses variables from the enclosing scope.

            Gives:
                None: Updates the controls of the decks list.
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

            Takes:
                e (ft.ControlEvent): The event object from the button click.

            Gives:
                None: Updates the deck list and refreshes the page.
            """
            self.revision_service.scan_folder()
            nonlocal deck_counts, total_pending
            deck_counts, total_pending = self.revision_service.get_deck_stats()
            update_decks_list()
            deck_dropdown.options = [ft.dropdown.Option("ALL")] + [ft.dropdown.Option(d) for d in sorted(deck_counts.keys())]
            deck_dropdown.value = "ALL"
            self.page.update()

        def start_fsrs_session(cards):
            """
            Starts the revision session with FSRS v6 ratings.

            Takes:
                cards (list): A list of dictionaries containing card information.

            Gives:
                None: Shows a dialog to review cards.
            """
            current_index = 0
            total_cards = len(cards)
            
            card_text = ft.Markdown(
                cards[current_index]["question"], 
                extension_set=ft.MarkdownExtensionSet.GITHUB_FLAVORED,
                auto_follow_links=True,
                md_style_sheet=ft.MarkdownStyleSheet(
                    code_text_style=ft.TextStyle(
                        bgcolor="#2E2E2E",
                        color="#EB5757",
                        font_family="monospace",
                        weight=ft.FontWeight.BOLD,
                        size=14,
                    )
                )
            )
            answer_text = ft.Markdown(
                cards[current_index]["answer"], 
                extension_set=ft.MarkdownExtensionSet.GITHUB_FLAVORED,
                auto_follow_links=True,
                visible=False,
                md_style_sheet=ft.MarkdownStyleSheet(
                    code_text_style=ft.TextStyle(
                        bgcolor="#2E2E2E",
                        color="#EB5757",
                        font_family="monospace",
                        weight=ft.FontWeight.BOLD,
                        size=14,
                    )
                )
            )
            
            progress_text = ft.Text(f"Card 1 of {total_cards}", size=14, color=ft.Colors.GREY_400)
            
            def show_answer(e):
                """
                Reveals the answer and shows FSRS rating buttons.

                Takes:
                    e (ft.ControlEvent): The event object from the button click.

                Gives:
                    None: Updates the visibility of controls on the page.
                """
                answer_text.visible = True
                show_btn.visible = False
                rating_row.visible = True
                self.page.update()
                
            def rate_card(e, quality):
                """
                Processes the card rating using FSRS v6 and advances.

                Takes:
                    e (ft.ControlEvent): The event object from the button click.
                    quality (int): The rating provided by the user.

                Gives:
                    None: Schedules the card and updates the UI for the next card.
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

            show_btn = ft.Button("Show Answer", on_click=show_answer, height=50)
            
            rating_row = ft.Row([
                ft.Button("Again", on_click=lambda e: rate_card(e, 1), bgcolor=ft.Colors.RED_700, color=ft.Colors.WHITE),
                ft.Button("Hard", on_click=lambda e: rate_card(e, 2), bgcolor=ft.Colors.ORANGE_700, color=ft.Colors.WHITE),
                ft.Button("Good", on_click=lambda e: rate_card(e, 3), bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE),
                ft.Button("Easy", on_click=lambda e: rate_card(e, 4), bgcolor=ft.Colors.BLUE_700, color=ft.Colors.WHITE)
            ], visible=False, alignment=ft.MainAxisAlignment.CENTER, spacing=15)

            dialog = ft.AlertDialog(
                modal=True,
                title=ft.Row([ft.Text("Revision Session"), progress_text], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                content=ft.Container(
                    content=ft.Column([
                        ft.Container(content=card_text, padding=20, alignment=ft.Alignment.CENTER),
                        ft.Divider(height=1, color=ft.Colors.GREY_800),
                        ft.Container(
                            content=ft.Column([answer_text], scroll=ft.ScrollMode.AUTO, expand=True), 
                            padding=20, 
                            alignment=ft.Alignment.TOP_LEFT, 
                            expand=True
                        )
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

        def on_revise(e):
            """
            Handles the revise button click event.

            Takes:
                e (ft.ControlEvent): The event object from the button click.

            Gives:
                None: Starts the revision session or shows a dialog if no cards.
            """
            deck = deck_dropdown.value
            cards = self.revision_service.revise_deck(deck)
            if not cards:
                dialog = ft.AlertDialog(title=ft.Text("No pending cards"), content=ft.Text("You are all caught up for this deck!"))
                self.page.show_dialog(dialog)
                return
                
            start_fsrs_session(cards)

        rescan_btn = ft.IconButton(icon=ft.Icons.SYNC, on_click=on_rescan, tooltip="Rescan Folder")
        revise_btn = ft.Button("Start Revision", on_click=on_revise, height=50)

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

    def _overview_tab(self):
        """
        Builds the Overview tab UI with pre-rendered analytics.

        Takes:
            None: Uses the statistics service.

        Gives:
            ft.Column: A scrollable column containing metrics and charts.
        """
        charts_container = ft.Column(expand=True, spacing=40)

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

        data = self.stats_service.give_overview()
        overview_data = data["overview_data"]

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

        charts_container.controls.extend(rows)

        return ft.Column([
            ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
            charts_container,
            ft.Container(expand=True)
        ], expand=True, scroll=ft.ScrollMode.AUTO, spacing=30)

    def _settings_tab(self):
        """
        Builds the Settings tab UI for managing multiple flashcard directories.

        Takes:
            None: Uses internal settings service.

        Gives:
            ft.Container: A container with the multi-path settings UI.
        """
        current_paths = self.settings_service.get_folder_paths()
        
        paths_list = ft.Column(spacing=10)
        
        def delete_path_confirmed(path):
            new_paths = [p for p in current_paths if p != path]
            self.settings_service.update_folder_paths(new_paths)
            self.view(selected_index=2)
            snack = ft.SnackBar(ft.Text(f"Path removed: {path}"))
            self.page.overlay.append(snack)
            snack.open = True
            self.page.update()

        def show_delete_dialog(path):
            dialog = ft.AlertDialog(
                title=ft.Text("Confirm Deletion"),
                content=ft.Text(f"This action will cause to delete any flashcards inside database associated with this path: '{path}'. This cannot be undone. Are you sure?"),
                actions=[
                    ft.TextButton("Yes", on_click=lambda _: (self.page.pop_dialog(), delete_path_confirmed(path))),
                    ft.TextButton("No", on_click=lambda _: self.page.pop_dialog()),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )
            self.page.show_dialog(dialog)

        for path in current_paths:
            paths_list.controls.append(
                ft.Row([
                    ft.Icon(ft.Icons.FOLDER, color=ft.Colors.AMBER_400),
                    ft.Text(path, expand=True, size=16),
                    ft.IconButton(
                        icon=ft.Icons.DELETE_OUTLINE,
                        icon_color=ft.Colors.RED_400,
                        tooltip="Remove Path",
                        on_click=lambda e, p=path: show_delete_dialog(p)
                    )
                ], alignment=ft.MainAxisAlignment.START)
            )

        new_path_input = ft.TextField(
            label="New Flashcards Directory",
            hint_text="e.g., /path/to/your/markdown/notes",
            expand=True
        )

        def add_path(e):
            val = new_path_input.value.strip()
            if not val:
                return
            
            if len(current_paths) >= 10:
                snack = ft.SnackBar(ft.Text("Limit reached! You can only have up to 10 paths."))
                self.page.overlay.append(snack)
                snack.open = True
                self.page.update()
                return

            if val in current_paths:
                snack = ft.SnackBar(ft.Text("This path is already added!"))
                self.page.overlay.append(snack)
                snack.open = True
                self.page.update()
                return

            if not os.path.exists(val):
                snack = ft.SnackBar(ft.Text("Warning: Directory does not exist! It will be added but no cards will be scanned."))
                self.page.overlay.append(snack)
                snack.open = True
            
            new_paths = current_paths + [val]
            self.settings_service.update_folder_paths(new_paths)
            self.view(selected_index=2)
            if os.path.exists(val):
                snack = ft.SnackBar(ft.Text("Path added and folder scanned!"))
                self.page.overlay.append(snack)
                snack.open = True
                self.page.update()

        add_btn = ft.Button("Add Path", on_click=add_path, height=50)

        return ft.Container(
            content=ft.Column([
                ft.Text("Flashcards Root Directories", size=18, weight=ft.FontWeight.BOLD),
                ft.Text("Specify the root folders where your markdown flashcards are stored. You can add up to 10 paths.", color=ft.Colors.GREY_400),
                ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
                paths_list,
                ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
                ft.Row([new_path_input, add_btn], alignment=ft.MainAxisAlignment.START, spacing=20)
            ], scroll=ft.ScrollMode.AUTO),
            padding=30,
            alignment=ft.Alignment.TOP_LEFT
        )
