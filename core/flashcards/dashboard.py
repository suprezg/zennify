"""
File Name: dashboard.py
Purpose: User interface for the Flashcards feature with centered layout and list tiles.
"""

import os
import flet as ft
import datetime
import io
import base64
import matplotlib
import matplotlib.pyplot as plt
from core.flashcards.service import FlashcardRevision, FlashcardSettings, FlashcardStorage, FlashcardStatistics
from core.shared.configurator import ConfigManager

matplotlib.use("agg")


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
                        ft.Button("Go to Revision", on_click=lambda _: self.view(0), height=50)
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    expand=True,
                    alignment=ft.Alignment.CENTER
                )
            ], expand=True)

        # 2. Charts Preparation logic
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

        # 1. Ease Factor Distribution (Bar)
        fig1, ax1 = plt.subplots(figsize=(7, 4))
        ax1.set_facecolor(bg_color)
        labels, counts = zip(*g_stats["difficulty_dist"])
        ax1.bar(labels, counts, color="#42A5F5")
        chart1_base64 = fig_to_base64(fig1)
        mode_diff = max(g_stats["difficulty_dist"], key=lambda x: x[1])

        # 2. Memory Stability (Bar)
        fig2, ax2 = plt.subplots(figsize=(7, 4))
        ax2.set_facecolor(bg_color)
        s_labels, s_counts = zip(*d_stats["stability"])
        ax2.bar(s_labels, s_counts, color="#26C6DA")
        chart2_base64 = fig_to_base64(fig2)
        mature_count = next((c for l, c in d_stats["stability"] if l == "Mature"), 0)

        # 3. 30-Day Forecast (Line)
        fig3, ax3 = plt.subplots(figsize=(7, 4))
        ax3.set_facecolor(bg_color)
        f_dates, f_counts = zip(*g_stats["forecast"])
        f_short_dates = [d[-5:] for d in f_dates]
        ax3.plot(f_short_dates, f_counts, color="#FFCA28", marker="o", linewidth=2)
        for i, t in enumerate(ax3.get_xticklabels()):
            if i % 5 != 0: t.set_visible(False)
        chart3_base64 = fig_to_base64(fig3)
        next_rev_count = g_stats["forecast"][0][1]

        # 4. Card Freshness (Pie)
        fig4, ax4 = plt.subplots(figsize=(7, 4))
        ax4.set_facecolor(bg_color)
        p_labels, p_counts = zip(*d_stats["freshness"])
        p_data = [(l, c) for l, c in zip(p_labels, p_counts) if c > 0]
        if p_data:
            p_labels, p_counts = zip(*p_data)
            ax4.pie(p_counts, labels=p_labels, autopct='%1.1f%%', colors=["#66BB6A", "#FFA726", "#EF5350"], textprops={'color':"w"})
        else:
            ax4.text(0.5, 0.5, "No Data", ha='center', va='center', color="white")
        chart4_base64 = fig_to_base64(fig4)
        review_count = next((c for l, c in d_stats["freshness"] if l == "Review"), 0)
        total_d_cards = sum(p_counts)
        rev_pc = round((review_count / total_d_cards * 100), 1) if total_d_cards > 0 else 0

        # Helper for Chart/Metric Rows
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

        # 4. Layout
        return ft.Column([
            ft.Container(content=metrics_row, padding=20),
            ft.Divider(height=1, color=ft.Colors.GREY_800),
            
            # Metric Rows
            row_builder(
                "Active Knowledge",
                ft.Container(content=ft.Text(f"{g_stats['active_knowledge']}%", size=60, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_ACCENT), height=300, alignment=ft.Alignment.CENTER),
                "Active Knowledge represents the total volume of information you are expected to remember right now. It is calculated by summing the retrievability (probability of recall) across all cards in your collection. Unlike total card count, this weights cards by how 'fresh' they are in your mind.",
                f"You are currently effectively retaining {g_stats['active_knowledge']}% of your entire knowledge base."
            ),
            
            row_builder(
                "Success Rate",
                ft.Container(content=ft.Text(f"{d_stats['success_rate']}%", size=60, weight=ft.FontWeight.BOLD, color=ft.Colors.CYAN_ACCENT), height=300, alignment=ft.Alignment.CENTER),
                "Success Rate estimate predicts how likely you are to correctly answer a card if it were shown right now. This is a real-time estimation of your recall performance across your entire active deck based on the FSRS decay model.",
                f"Based on your memory stability, you are likely to recall {d_stats['success_rate']}% of your active cards."
            ),
            
            row_builder(
                "Retention Rate",
                ft.Container(content=ft.Text(f"{d_stats['retention_rate']}%", size=60, weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER_ACCENT), height=300, alignment=ft.Alignment.CENTER),
                "Retention Rate is the average retrievability of all cards that have been learned. FSRS uses this to optimize your study schedule. A high retention rate means you remember things well but might be over-studying; a low rate means you're forgetting too much.",
                f"Your average memory strength for learned material is currently at {d_stats['retention_rate']}%."
            ),
            
            ft.Divider(height=40, color=ft.Colors.TRANSPARENT),
            
            # Chart Rows
            row_builder(
                "Ease Factor Distribution", 
                ft.Image(src=chart1_base64, height=300, fit=ft.BoxFit.CONTAIN),
                "The Ease Factor determines how quickly review intervals grow. This distribution shows the difficulty profile of your cards. Higher ease means concepts are mastered, while lower ease indicates material requiring more frequent repetition.",
                f"Your most common difficulty level is '{mode_diff[0]}' with {mode_diff[1]} cards."
            ),
            
            row_builder(
                "Memory Stability (Strength)",
                ft.Image(src=chart2_base64, height=300, fit=ft.BoxFit.CONTAIN),
                "Memory Stability represents the time it will take for your retention to drop to 90%. Cards are categorized into maturity buckets: New, Learning, Review, and Mature. Higher stability means stronger long-term memory consolidation.",
                f"You have {mature_count} mature cards established in your long-term memory."
            ),
            
            row_builder(
                "30-Day Review Forecast",
                ft.Image(src=chart3_base64, height=300, fit=ft.BoxFit.CONTAIN),
                "The Forecast predicts your future workload by calculating when cards will become due. This helps you plan your study sessions and prepare for potential spikes in your review schedule over the next 30 days.",
                f"You have {next_rev_count} cards scheduled for your next review session."
            ),
            
            row_builder(
                "Card Status Distribution",
                ft.Image(src=chart4_base64, height=300, fit=ft.BoxFit.CONTAIN),
                "This chart provides a snapshot of your progress. 'New' cards are unexplored, 'Learning' cards are being acquired, and 'Review' cards are established. A healthy learning cycle moves cards steadily toward the Review phase.",
                f"Currently, {rev_pc}% of your deck has successfully reached the long-term Review phase."
            )
            
            ], expand=True, scroll=ft.ScrollMode.AUTO, spacing=40)

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

    def _start_fsrs_session(self, cards):
        """
        Starts the revision session with FSRS v6 ratings.

        Takes: cards (list)
        Gives: None
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

        update_btn = ft.Button("Update & Rescan", on_click=update_path, height=50)

        return ft.Container(
            content=ft.Column([
                ft.Text("Flashcards Root Directory", size=18),
                ft.Text("Specify the root folder where your markdown flashcards are stored.", color=ft.Colors.GREY_400),
                ft.Row([path_input, update_btn], alignment=ft.MainAxisAlignment.START, spacing=20)
            ], scroll=ft.ScrollMode.AUTO),
            padding=30,
            alignment=ft.Alignment.TOP_LEFT
        )
