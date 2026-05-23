"""
File Name: service.py
Purpose: Logic and data management for the Flashcards feature using FSRS v6.
"""

import os
import hashlib
import datetime
from fsrs import Scheduler, Card, Rating
from core.shared.storage import StorageManager
from core.shared.configurator import ConfigManager


class FlashcardStorage:
    """
    Handles database operations for flashcard records.
    """

    def __init__(self):
        """
        Initializes the storage manager.

        Takes: None
        Gives: None
        """
        self.storage = StorageManager()

    def read_entries(self, query, params=()):
        """
        Executes a database read query.

        Takes: query (str), params (tuple)
        Gives: list of records
        """
        return self.storage.read(query, params)

    def write_entries(self, query, params=()):
        """
        Executes a database write query.

        Takes: query (str), params (tuple)
        Gives: None
        """
        self.storage.write(query, params)


class FlashcardSettings:
    """
    Manages configuration settings for the flashcard module.
    """

    def __init__(self):
        """
        Initializes the configuration manager.

        Takes: None
        Gives: None
        """
        self.config_manager = ConfigManager()

    def change_folder(self, new_folder_path):
        """
        Updates the target folder and triggers a directory scan.

        Takes: new_folder_path (str)
        Gives: None
        """
        self.config_manager.update_value("flashcard", "folder_path", new_folder_path)
        revision = FlashcardRevision()
        revision.scan_folder()


class FlashcardStatistics:
    """
    Processes flashcard data for overview visualizations.
    """

    def __init__(self):
        """
        Initializes the storage and configuration managers.

        Takes: None
        Gives: None
        """
        self.storage = FlashcardStorage()
        self.config_manager = ConfigManager()

    def give_overview(self, deck_name="ALL"):
        """
        Calculates analytics for global and specific decks.

        Takes: deck_name (str)
        Gives: dict
        """
        # Fetch global data for top level stats
        all_cards = self.storage.read_entries("SELECT stability, difficulty, state, next_review, last_review, deck_name FROM flashcard")
        
        # Global Metrics
        
        now = datetime.datetime.now(datetime.timezone.utc)
        total_cards = len(all_cards)
        
        # A card is considered revised if it has a non-null stability
        revised_cards = [c for c in all_cards if c[0] is not None]
        revised_count = len(revised_cards)
        
        # Calculate Retrievability (R = 0.9^(t/S)) and Active Knowledge (Sum of R)
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
                # Formula: R = 0.9^(t/S)
                r = (0.9 ** (t / stability)) if stability > 0 else 0
                total_retrievability += r
                sum_r_all += r
            except (ValueError, TypeError, ZeroDivisionError):
                continue

        # Active Knowledge % = (Sum of Retrievability / Total Cards) * 100
        active_knowledge_pc = (sum_r_all / total_cards * 100) if total_cards > 0 else 0
        # Retention Rate (Deck) = Average Retrievability of learned cards
        avg_retention = (total_retrievability / revised_count * 100) if revised_count > 0 else 0
        
        # Difficulty Distribution Histogram
        diff_dist = {"Very Easy": 0, "Easy": 0, "Medium": 0, "Hard": 0, "Very Hard": 0}
        for c in all_cards:
            if c[1] is None:
                continue
            d = c[1]
            if d < 2: diff_dist["Very Easy"] += 1
            elif d < 4: diff_dist["Easy"] += 1
            elif d < 6: diff_dist["Medium"] += 1
            elif d < 8: diff_dist["Hard"] += 1
            else: diff_dist["Very Hard"] += 1

        # Review Forecast (Next 30 days)
        forecast = {}
        for i in range(30):
            day = (now + datetime.timedelta(days=i)).strftime("%Y-%m-%d")
            forecast[day] = 0
            
        for c in all_cards:
            try:
                if not c[3]: continue
                # Only forecast cards that have been revised (stability is not None)
                if c[0] is None: continue
                due = datetime.datetime.fromisoformat(c[3])
                if due.tzinfo is None: due = due.replace(tzinfo=datetime.timezone.utc)
                if now <= due <= (now + datetime.timedelta(days=30)):
                    day = due.strftime("%Y-%m-%d")
                    forecast[day] = forecast.get(day, 0) + 1
            except (ValueError, TypeError):
                continue

        # Deck Specific Metrics
        deck_cards = all_cards if deck_name == "ALL" else [c for c in all_cards if c[5] == deck_name]
        
        # Freshness Ratio (Using Stability & State)
        freshness = {"New": 0, "Learning": 0, "Review": 0}
        # Maturity buckets (Stability based)
        stability_buckets = {"New": 0, "Learning": 0, "Review": 0, "Mature": 0}
        
        success_count = 0
        reviewed_in_deck = 0

        for c in deck_cards:
            stability, difficulty, state, next_review_str, last_review_str, _ = c
            
            # Freshness
            if stability is None: 
                freshness["New"] += 1
            elif state in (1, 3): 
                freshness["Learning"] += 1
            else: 
                freshness["Review"] += 1
            
            if stability is not None and stability > 0:
                reviewed_in_deck += 1
                # Retention/Success Estimate: Probability that R > 0.8
                lr = datetime.datetime.fromisoformat(last_review_str)
                if lr.tzinfo is None: lr = lr.replace(tzinfo=datetime.timezone.utc)
                t = (now - lr).days
                if (0.9 ** (t/stability)) > 0.8:
                    success_count += 1
            
            # Memory Stability Buckets
            try:
                if stability is None or not next_review_str or not last_review_str:
                    stability_buckets["New"] += 1
                    continue
                    
                nr = datetime.datetime.fromisoformat(next_review_str)
                lr = datetime.datetime.fromisoformat(last_review_str)
                interval = (nr - lr).days
                if interval <= 1: stability_buckets["New"] += 1
                elif interval <= 7: stability_buckets["Learning"] += 1
                elif interval <= 30: stability_buckets["Review"] += 1
                else: stability_buckets["Mature"] += 1
            except (ValueError, TypeError):
                stability_buckets["New"] += 1

        return {
            "global": {
                "active_knowledge": round(active_knowledge_pc, 1),
                "difficulty_dist": list(diff_dist.items()) if sum(diff_dist.values()) > 0 else [("None", 1)],
                "forecast": sorted(forecast.items()),
                "revised_count": revised_count
            },
            "deck": {
                "success_rate": round(success_count / reviewed_in_deck * 100, 1) if reviewed_in_deck > 0 else 0,
                "freshness": list(freshness.items()),
                "retention_rate": round(avg_retention, 1),
                "stability": list(stability_buckets.items()),
            },
            "available_decks": sorted(list(set(c[5] for c in all_cards)))
        }


class FlashcardRevision:
    """
    Handles logic for spaced repetition scheduling using FSRS v6 and folder scanning.
    """

    def __init__(self):
        """
        Initializes the revision services and FSRS scheduler.

        Takes: None
        Gives: None
        """
        self.storage = FlashcardStorage()
        self.config_manager = ConfigManager()
        self.sch = Scheduler()

    def scan_folder(self):
        """
        Scans the Directory and updates the flashcard table in database.

        Takes: None
        Gives: None
        """
        import re
        folder_path = self.config_manager.read_value("flashcard", "folder_path")
        if not folder_path or not os.path.exists(folder_path):
            return

        existing_cards = self.storage.read_entries("SELECT card_id, content_hash FROM flashcard")
        existing_map = {row[0]: row[1] for row in existing_cards}
        
        discovered_ids = set()

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

                    # Robustly extract frontmatter and body
                    match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)', content, re.DOTALL)
                    if not match:
                        continue
                    frontmatter, body = match.groups()
                    
                    # Search for tags in frontmatter
                    tags_match = re.search(r'^tags:\s*(.*)', frontmatter, re.MULTILINE | re.IGNORECASE)
                    if not tags_match:
                        continue
                    tags_line = tags_match.group(1).lower()
                    if 'flashcards' not in tags_line:
                        continue

                    # Split by heading taking care of newlines so we don't match internal '#' inside answers
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
                                self.storage.write_entries(
                                    "UPDATE flashcard SET content_hash = ?, deck_name = ? WHERE card_id = ?",
                                    (content_hash, deck_name, id_hash)
                                )
                        else:
                            now = datetime.datetime.now(datetime.timezone.utc)
                            card = Card()
                            self.storage.write_entries(
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
                self.storage.write_entries("DELETE FROM flashcard WHERE card_id = ?", (old_id,))

    def revise_deck(self, deck_name):
        """
        Gets cards which are up for revision.

        Takes: deck_name (str)
        Gives: list
        """
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        if deck_name.lower() == "all":
            query = "SELECT card_id, deck_name FROM flashcard WHERE next_review <= ?"
            params = (now,)
        else:
            query = "SELECT card_id, deck_name FROM flashcard WHERE deck_name = ? AND next_review <= ?"
            params = (deck_name, now)
            
        pending_records = self.storage.read_entries(query, params)
        if not pending_records:
            return []
            
        pending_ids = set(row[0] for row in pending_records)
        
        folder_path = self.config_manager.read_value("flashcard", "folder_path")
        cards_to_revise = []
        
        if not folder_path or not os.path.exists(folder_path):
            return cards_to_revise

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

        Takes: card_id (str), rating_val (int)
        Gives: None
        """
        card_data = self.storage.read_entries(
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
        
        self.storage.write_entries(
            """UPDATE flashcard SET 
                stability = ?, difficulty = ?, state = ?, next_review = ?, last_review = ? 
               WHERE card_id = ?""",
            (
                new_card.stability, new_card.difficulty, new_card.state, 
                new_card.due.isoformat(), now.isoformat(), card_id
            )
        )
