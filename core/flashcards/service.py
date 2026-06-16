"""
File Name: service.py
Purpose: Logic and data management for the Flashcards feature using FSRS v6.
"""

import os
import hashlib
import datetime
import io
import base64
import matplotlib
import matplotlib.pyplot as plt
from fsrs import Scheduler, Card, Rating
from core.shared.storage import StorageManager
from core.shared.configurator import ConfigManager

matplotlib.use("agg")

class FlashcardSettings:
    """
    Manages configuration settings for the flashcard module.
    """

    def __init__(self):
        """
        Initializes the configuration manager.

        Takes:
            None: Uses the default ConfigManager.

        Gives:
            None: Prepares the settings service.
        """
        self.config_manager = ConfigManager()

    def get_folder_paths(self):
        """
        Retrieves the flashcard folder paths from the configuration.
        Supports backward compatibility for single 'folder_path'.

        Takes:
            None: Uses the internal ConfigManager instance.

        Gives:
            list: A list of paths to the flashcard folders.
        """
        paths = self.config_manager.read_value("flashcard", "folder_paths")
        if paths is None:
            old_path = self.config_manager.read_value("flashcard", "folder_path")
            return [old_path] if old_path else []
        return paths

    def update_folder_paths(self, new_paths):
        """
        Updates the target folders and triggers a directory scan.

        Takes:
            new_paths (list): The new list of paths for the flashcards folders.

        Gives:
            None: Updates the config and triggers a scan.
        """
        self.config_manager.update_value("flashcard", "folder_paths", new_paths)
        FlashcardRevision().scan_folder()


class FlashcardStatistics:
    """
    Processes and aggregates flashcard data for visualization on the overview screen.
    """

    def __init__(self) :
        """
        Initializes the statistics service with storage and configuration managers.

        Takes:
            None: Uses the default StorageManager and ConfigManager.

        Gives:
            None: Prepares the service for data processing.
        """
        self.storage = StorageManager()
        self.config_manager = ConfigManager()

    def _fig_to_base64(self, fig, bg_color) :
        """
        Converts a Matplotlib figure into a base64 encoded string.

        Takes:
            fig (plt.Figure): The Matplotlib figure object to convert.
            bg_color (str): The background color for the saved figure.

        Gives:
            str: A base64 encoded PNG image string.
        """
        buf = io.BytesIO()
        fig.tight_layout(pad=1.5)
        fig.savefig(buf, format="png", bbox_inches="tight", facecolor=bg_color, dpi=100)
        plt.close(fig)
        return base64.b64encode(buf.getvalue()).decode("utf-8")

    def give_overview(self) :
        """
        Generates aggregated global statistics and pre-rendered charts for the overview screen.

        Takes:
            None: Processes all cards in the database.

        Gives:
            dict: A dictionary containing 'revised_count' and 'overview_data' (list of components).
        """
        all_cards = self.storage.read("SELECT stability, difficulty, state, next_review, last_review, deck_name FROM flashcard")
        
        now = datetime.datetime.now(datetime.timezone.utc)
        total_cards = len(all_cards)
        
        revised_cards = [c for c in all_cards if c[0] is not None]
        revised_count = len(revised_cards)
        has_enough_data = revised_count >= 5

        total_retrievability = 0
        sum_r_all = 0
        for c in all_cards:
            stability, difficulty, state, _, last_review_str, _ = c
            if stability is None or stability == 0:
                continue
                
            try:
                lr = datetime.datetime.fromisoformat(last_review_str)
                if lr.tzinfo is None: lr = lr.replace(tzinfo=datetime.timezone.utc)
                t = max(0, (now - lr).days)
                r = (0.9 ** (t / stability)) if stability > 0 else 0
                total_retrievability += r
                sum_r_all += r
            except (ValueError, TypeError, ZeroDivisionError):
                continue

        active_knowledge_pc = (sum_r_all / total_cards * 100) if total_cards > 0 else 0
        avg_retention = (total_retrievability / revised_count * 100) if revised_count > 0 else 0
        
        diff_dist = {"Very Easy": 0, "Easy": 0, "Medium": 0, "Hard": 0, "Very Hard": 0}
        for c in all_cards:
            if c[1] is not None:
                d = c[1]
                if d < 2: diff_dist["Very Easy"] += 1
                elif d < 4: diff_dist["Easy"] += 1
                elif d < 6: diff_dist["Medium"] += 1
                elif d < 8: diff_dist["Hard"] += 1
                else: diff_dist["Very Hard"] += 1
        
        mode_diff = max(diff_dist.items(), key=lambda x: x[1])

        forecast = {}
        for i in range(30):
            day = (now + datetime.timedelta(days=i)).strftime("%Y-%m-%d")
            forecast[day] = 0
            
        for c in all_cards:
            try:
                if c[0] is not None and c[3]:
                    due = datetime.datetime.fromisoformat(c[3])
                    if due.tzinfo is None: due = due.replace(tzinfo=datetime.timezone.utc)
                    if now <= due <= (now + datetime.timedelta(days=30)):
                        day = due.strftime("%Y-%m-%d")
                        forecast[day] = forecast.get(day, 0) + 1
            except (ValueError, TypeError):
                continue
        
        next_rev_count = forecast[now.strftime("%Y-%m-%d")] if now.strftime("%Y-%m-%d") in forecast else 0

        freshness = {"New": 0, "Learning": 0, "Review": 0}
        stability_buckets = {"New": 0, "Learning": 0, "Review": 0, "Mature": 0}
        success_count = 0

        for c in all_cards:
            stability, difficulty, state, next_review_str, last_review_str, _ = c
            if stability is None: 
                freshness["New"] += 1
            elif state in (1, 3): 
                freshness["Learning"] += 1
            else: 
                freshness["Review"] += 1
            
            if stability is not None and stability > 0:
                lr = datetime.datetime.fromisoformat(last_review_str)
                if lr.tzinfo is None: lr = lr.replace(tzinfo=datetime.timezone.utc)
                t = (now - lr).days
                if (0.9 ** (t/stability)) > 0.8:
                    success_count += 1
            
            try:
                if stability is None or not next_review_str or not last_review_str:
                    stability_buckets["New"] += 1
                else:
                    nr = datetime.datetime.fromisoformat(next_review_str)
                    lr = datetime.datetime.fromisoformat(last_review_str)
                    interval = (nr - lr).days
                    if interval <= 1: stability_buckets["New"] += 1
                    elif interval <= 7: stability_buckets["Learning"] += 1
                    elif interval <= 30: stability_buckets["Review"] += 1
                    else: stability_buckets["Mature"] += 1
            except (ValueError, TypeError):
                stability_buckets["New"] += 1

        success_rate = round(success_count / revised_count * 100, 1) if revised_count > 0 else 0
        mature_count = stability_buckets["Mature"]
        review_count = freshness["Review"]
        rev_pc = round((review_count / total_cards * 100), 1) if total_cards > 0 else 0

        bg_color = "#111418"
        plt.rcParams.update({
            "text.color": "white",
            "axes.labelcolor": "white",
            "xtick.color": "white",
            "ytick.color": "white",
            "axes.edgecolor": "white",
        })

        fig1, ax1 = plt.subplots(figsize=(7, 4))
        ax1.set_facecolor(bg_color)
        if has_enough_data:
            labels, counts = zip(*diff_dist.items())
            ax1.bar(labels, counts, color="#42A5F5")
        else:
            ax1.text(0.5, 0.5, "Not Enough Data", ha='center', va='center', color="white")
        chart1_base64 = self._fig_to_base64(fig1, bg_color)

        fig2, ax2 = plt.subplots(figsize=(7, 4))
        ax2.set_facecolor(bg_color)
        if has_enough_data:
            s_labels, s_counts = zip(*stability_buckets.items())
            ax2.bar(s_labels, s_counts, color="#26C6DA")
        else:
            ax2.text(0.5, 0.5, "Not Enough Data", ha='center', va='center', color="white")
        chart2_base64 = self._fig_to_base64(fig2, bg_color)

        fig3, ax3 = plt.subplots(figsize=(7, 4))
        ax3.set_facecolor(bg_color)
        if has_enough_data:
            f_sorted = sorted(forecast.items())
            f_dates, f_counts = zip(*f_sorted)
            f_short_dates = [d[-5:] for d in f_dates]
            ax3.plot(f_short_dates, f_counts, color="#FFCA28", marker="o", linewidth=2)
            for i, t in enumerate(ax3.get_xticklabels()):
                if i % 5 != 0: t.set_visible(False)
        else:
            ax3.text(0.5, 0.5, "Not Enough Data", ha='center', va='center', color="white")
        chart3_base64 = self._fig_to_base64(fig3, bg_color)

        fig4, ax4 = plt.subplots(figsize=(7, 4))
        ax4.set_facecolor(bg_color)
        p_data = [(l, c) for l, c in freshness.items() if c > 0]
        if has_enough_data and p_data:
            p_labels, p_counts = zip(*p_data)
            ax4.pie(p_counts, labels=p_labels, autopct='%1.1f%%', colors=["#66BB6A", "#FFA726", "#EF5350"], textprops={'color':"w"})
        else:
            ax4.text(0.5, 0.5, "Not Enough Data", ha='center', va='center', color="white")
        chart4_base64 = self._fig_to_base64(fig4, bg_color)

        overview_data = [
            {
                "title": "Active Knowledge",
                "type": "text",
                "value": f"{round(active_knowledge_pc, 1)}%" if has_enough_data else "N/A",
                "explanation": "Active Knowledge represents the estimated amount of information you can recall at this exact moment. It is calculated using the FSRS algorithm, which determines the probability of recall for every card in your collection. Unlike total card count, this metric weights each card by its current 'retrievability', giving you a realistic measure of your true knowledge volume.",
                "insight": f"You are currently effectively retaining {round(active_knowledge_pc, 1)}% of your entire knowledge base." if has_enough_data else "Complete more revisions to calculate knowledge retention."
            },
            {
                "title": "Success Rate",
                "type": "text",
                "value": f"{success_rate}%" if has_enough_data else "N/A",
                "explanation": "The Success Rate provides a real-time prediction of your performance. It estimates the percentage of your active cards that you would correctly answer if you were tested right now. This is based on the decay of memory over time; as cards approach their due date, their success probability drops, reflecting the overall health of your immediate recall.",
                "insight": f"Based on your memory stability, you are likely to recall {success_rate}% of your active cards." if has_enough_data else "Insufficient revision history to estimate recall success."
            },
            {
                "title": "Retention Rate",
                "type": "text",
                "value": f"{round(avg_retention, 1)}%" if has_enough_data else "N/A",
                "explanation": "Retention Rate measures the average retrievability of all cards you have already learned. In spaced repetition, optimal retention is usually around 90%. If this number is very high, you may be over-studying and seeing cards too often; if it is low, you are forgetting too much. This helps you balance memory strength with time efficiency.",
                "insight": f"Your average memory strength for learned material is currently at {round(avg_retention, 1)}%." if has_enough_data else "Study more cards to establish a baseline retention rate."
            },
            {
                "title": "Ease Factor Distribution",
                "type": "chart",
                "image_base64": chart1_base64,
                "explanation": "The Ease Factor distribution shows the complexity profile of your flashcard collection. FSRS assigns a difficulty value to each card based on your past ratings. This histogram helps you identify if your deck consists mostly of mastered concepts or if you are struggling with 'Hard' cards that require more cognitive effort.",
                "insight": f"Your most common difficulty level is '{mode_diff[0]}' with {mode_diff[1]} cards." if has_enough_data else "No difficulty distribution data available."
            },
            {
                "title": "Memory Stability (Strength)",
                "type": "chart",
                "image_base64": chart2_base64,
                "explanation": "Memory Stability represents the 'strength' of your long-term memory. It is the estimated time (in days) it takes for your recall probability to drop to 90%. Mature cards have very high stability, meaning they are deeply consolidated and will not need to be reviewed for months or even years.",
                "insight": f"You have {mature_count} mature cards established in your long-term memory." if has_enough_data else "Stability metrics require at least 5 card revisions."
            },
            {
                "title": "30-Day Review Forecast",
                "type": "chart",
                "image_base64": chart3_base64,
                "explanation": "The 30-Day Review Forecast is a predictive tool that calculates exactly when each card in your collection will next become due. By analyzing the stability of every card, it projects your upcoming workload day-by-day, allowing you to anticipate 'review spikes' and plan your study sessions in advance.",
                "insight": f"You have {next_rev_count} cards scheduled for your next review session." if has_enough_data else "Forecast will be available after your first revisions."
            },
            {
                "title": "Card Status Distribution",
                "type": "chart",
                "image_base64": chart4_base64,
                "explanation": "This chart visualizes the lifecycle of your learning process. Cards move from 'New' (unseen) to 'Learning' (initial acquisition) and eventually to 'Review' (established knowledge). A healthy distribution shows a steady flow of cards into the Review phase, indicating successful long-term retention.",
                "insight": f"Currently, {rev_pc}% of your deck has successfully reached the long-term Review phase." if has_enough_data else "Revise cards to move them through status phases."
            }
        ]

        return {"revised_count": revised_count, "overview_data": overview_data}


class FlashcardRevision:
    """
    Handles logic for spaced repetition scheduling using FSRS v6 and folder scanning.
    """

    def __init__(self):
        """
        Initializes the revision services and FSRS scheduler.

        Takes:
            None: Initializes the required managers and scheduler.

        Gives:
            None: Prepares the revision service.
        """
        self.storage = StorageManager()
        self.config_manager = ConfigManager()
        self.sch = Scheduler()

    def scan_folder(self):
        """
        Scans all configured directories and updates the flashcard table in database.

        Takes:
            None: Uses the configured folder paths.

        Gives:
            None: Updates the database with discovered flashcards.
        """
        import re
        folder_paths = FlashcardSettings().get_folder_paths()
        if not folder_paths:
            return

        existing_cards = self.storage.read("SELECT card_id, content_hash FROM flashcard")
        existing_map = {row[0]: row[1] for row in existing_cards}
        
        discovered_ids = set()

        for folder_path in folder_paths:
            if not os.path.exists(folder_path):
                continue

            for root, _, files in os.walk(folder_path):
                for file in files:
                    if file.endswith(".md"):
                        file_path = os.path.join(root, file)
                        deck_name = os.path.splitext(file)[0]
                        
                        try:
                            with open(file_path, "r", encoding="utf-8") as f:
                                content = f.read()
                        except Exception:
                            continue

                        match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)', content, re.DOTALL)
                        if not match:
                            continue
                        frontmatter, body = match.groups()
                        
                        tags_match = re.search(r'^tags:\s*(.*)', frontmatter, re.MULTILINE | re.IGNORECASE)
                        if not tags_match:
                            continue
                        tags_line = tags_match.group(1).lower()
                        if 'flashcards' not in tags_line:
                            continue

                        parts = re.split(r'\n#\s+', '\n' + body)
                        for part in parts[1:]:
                            lines = part.strip().split("\n")
                            if not lines:
                                continue
                            question = lines[0].strip()
                            answer = "\n".join(lines[1:]).strip()
                            
                            if not question:
                                continue
                            
                            id_hash = hashlib.md5(question.encode('utf-8')).hexdigest()
                            content_hash = hashlib.md5((question + answer).encode('utf-8')).hexdigest()
                            discovered_ids.add(id_hash)

                            if id_hash in existing_map:
                                if existing_map[id_hash] != content_hash:
                                    self.storage.write(
                                        "UPDATE flashcard SET content_hash = ?, deck_name = ? WHERE card_id = ?",
                                        (content_hash, deck_name, id_hash)
                                    )
                            else:
                                now = datetime.datetime.now(datetime.timezone.utc)
                                card = Card()
                                self.storage.write(
                                    """INSERT INTO flashcard (
                                        card_id, content_hash, deck_name, stability, difficulty, 
                                        state, next_review, last_review
                                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                                    (
                                        id_hash, content_hash, deck_name, card.stability, card.difficulty,
                                        int(card.state), now.isoformat(), now.isoformat()
                                    )
                                )
        
        for old_id in existing_map.keys():
            if old_id not in discovered_ids:
                self.storage.write("DELETE FROM flashcard WHERE card_id = ?", (old_id,))

    def revise_deck(self, deck_name):
        """
        Gets cards which are up for revision.

        Takes:
            deck_name (str): The name of the deck to revise, or "all" for all decks.

        Gives:
            list: A list of dictionaries containing card information.
        """
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        if deck_name.lower() == "all":
            query = "SELECT card_id, deck_name FROM flashcard WHERE next_review <= ?"
            params = (now,)
        else:
            query = "SELECT card_id, deck_name FROM flashcard WHERE deck_name = ? AND next_review <= ?"
            params = (deck_name, now)
            
        pending_records = self.storage.read(query, params)
        if not pending_records:
            return []
            
        pending_ids = set(row[0] for row in pending_records)
        
        folder_paths = FlashcardSettings().get_folder_paths()
        cards_to_revise = []
        
        if not folder_paths:
            return cards_to_revise

        for folder_path in folder_paths:
            if not os.path.exists(folder_path):
                continue

            for root, _, files in os.walk(folder_path):
                for file in files:
                    if file.endswith(".md"):
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, "r", encoding="utf-8") as f:
                                content = f.read()
                        except Exception:
                            continue
                            
                        if "tags: flashcards" not in content.lower():
                            continue
                            
                        parts = content.split("# ")
                        for part in parts[1:]:
                            lines = part.strip().split("\n")
                            if not lines:
                                continue
                            question = lines[0].strip()
                            answer = "\n".join(lines[1:]).strip()
                            
                            id_hash = hashlib.md5(question.encode('utf-8')).hexdigest()
                            if id_hash in pending_ids:
                                cards_to_revise.append({
                                    "id": id_hash,
                                    "question": question,
                                    "answer": answer,
                                    "deck": os.path.splitext(file)[0]
                                })
                            
        return cards_to_revise

    def schdule_card(self, card_id, rating_val):
        """
        Updates the card values using FSRS v6.

        Takes:
            card_id (str): The unique identifier of the flashcard.
            rating_val (int): The rating provided by the user.

        Gives:
            None: Updates the card scheduling data in the database.
        """
        card_data = self.storage.read(
            "SELECT stability, difficulty, state, last_review FROM flashcard WHERE card_id = ?", 
            (card_id,)
        )
        if not card_data:
            return
            
        stability, difficulty, state_val, last_review_str = card_data[0]
        
        last_review = datetime.datetime.fromisoformat(last_review_str)
        if last_review.tzinfo is None:
            last_review = last_review.replace(tzinfo=datetime.timezone.utc)

        card = Card(
            stability=stability,
            difficulty=difficulty,
            state=state_val,
            last_review=last_review
        )
        
        now = datetime.datetime.now(datetime.timezone.utc)
        rating = Rating(rating_val)
        
        new_card, review_log = self.sch.review_card(card, rating, now)
        
        self.storage.write(
            """UPDATE flashcard SET 
                stability = ?, difficulty = ?, state = ?, next_review = ?, last_review = ? 
               WHERE card_id = ?""",
            (
                new_card.stability, new_card.difficulty, new_card.state, 
                new_card.due.isoformat(), now.isoformat(), card_id
            )
        )

    def get_deck_stats(self):
        """
        Retrieves counts of pending cards per deck.

        Takes:
            None: Queries the database for pending revisions.

        Gives:
            tuple: A dictionary of pending counts per deck and the total count.
        """
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        cards = self.storage.read("SELECT deck_name FROM flashcard WHERE next_review <= ?", (now,))
        deck_counts = {}
        for card in cards:
            deck = card[0]
            deck_counts[deck] = deck_counts.get(deck, 0) + 1
        return deck_counts, len(cards)
