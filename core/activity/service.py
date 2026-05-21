"""
File Name: service.py
Purpose: Logic and data management for the Activity Tracker feature.
"""

import json
import os
import subprocess
from core.shared.storage import StorageManager


class ActivityStorage:
    """
    Handles database operations for activity records.
    """

    def __init__(self):
        """
        Initializes the storage manager.
        """
        self.storage = StorageManager()

    def read_entries(self, month, year):
        """
        Reads activity entries for a given month and year.

        Takes: month (str), year (str)
        Gives: list of activity records
        """
        pattern = f"{year}-{month}-%"
        query = "SELECT * FROM activity WHERE date LIKE ? ORDER BY date ASC, start_time ASC"
        return self.storage.read(query, (pattern,))

    def write_entry(self, date, start_time, end_time, description, tag, is_productive, retribution):
        """
        Writes a new activity entry to the database.

        Takes: date (str), start_time (str), end_time (str), description (str), tag (str), is_productive (bool), retribution (int)
        Gives: None
        """
        query = """
        INSERT INTO activity (date, start_time, end_time, description, tag, is_productive, retribution)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        self.storage.write(query, (date, start_time, end_time, description, tag, is_productive, retribution))

    def get_recent_tags(self):
        """
        Retrieves unique tags previously used in activities.

        Takes: None
        Gives: list of str
        """
        query = "SELECT DISTINCT tag FROM activity ORDER BY tag ASC"
        rows = self.storage.read(query)
        return [row[0] for row in rows]

    def get_last_entry(self):
        """
        Retrieves the most recent activity entry.

        Takes: None
        Gives: tuple or None
        """
        query = "SELECT * FROM activity ORDER BY session_id DESC LIMIT 1"
        rows = self.storage.read(query)
        return rows[0] if rows else None


class ActivitySettings:
    """
    Manages configuration settings for the activity module.
    """

    def __init__(self):
        """
        Initializes the config file path using ZENNIFY_CONFIG_PATH.

        Takes: None
        Gives: None
        """
        self.config_path = os.getenv("ZENNIFY_CONFIG_PATH")
        if not self.config_path:
            self.config_path = os.path.join(os.getcwd(), "config.json")

    def read_config(self):
        """
        Reads the activity configuration from config.json.

        Takes: None
        Gives: dict containing activity_config
        """
        if os.path.exists(self.config_path):
            with open(self.config_path, "r") as f:
                config = json.load(f)
                return config.get("activity_config", {})
        return {}

    def _update_config(self, key, value):
        """
        Helper to update a specific key in activity_config within config.json.

        Takes: key (str), value (any)
        Gives: None
        """
        if os.path.exists(self.config_path):
            with open(self.config_path, "r") as f:
                config = json.load(f)

            config["activity_config"][key] = value

            with open(self.config_path, "w") as f:
                json.dump(config, f, indent=4)

    def toggle_service(self, enable):
        """
        Enables or disables the background systemd service.

        Takes: enable (bool)
        Gives: None
        """
        state = "enable" if enable else "disable"
        try:
            subprocess.run(["systemctl", "--user", state, "--now", "zennify-activity.service"], check=True)
            self._update_config("service_status", enable)
        except subprocess.CalledProcessError:
            pass

    def change_popup_interval_timer(self, new_interval):
        """
        Updates the popup interval timer in config.json.

        Takes: new_interval (str)
        Gives: None
        """
        self._update_config("popup_interval_timer", new_interval)

    def change_popup_visible_timer(self, new_timer):
        """
        Updates the popup visible timer in config.json.

        Takes: new_timer (str)
        Gives: None
        """
        self._update_config("popup_visible_timer", new_timer)

    def update_streak_data(self, streak, multiplier):
        """
        Updates the streak and multiplier in config.json.

        Takes: streak (int), multiplier (float)
        Gives: None
        """
        if os.path.exists(self.config_path):
            with open(self.config_path, "r") as f:
                config = json.load(f)

            config["activity_config"]["streak"] = streak
            config["activity_config"]["multiplier"] = multiplier

            with open(self.config_path, "w") as f:
                json.dump(config, f, indent=4)


class ActivityStatistics:
    """
    Processes activity data for overview visualizations.
    """

    def __init__(self):
        """
        Initializes the storage manager.
        """
        self.storage = ActivityStorage()

    def give_overview(self, month, year):
        """
        Processes data to output aggregated statistics for the overview screen.

        Takes: month (str), year (str)
        Gives: dict containing processed statistics (tags, productivity ratio, etc.)
        """
        entries = self.storage.read_entries(month, year)

        productive_count = sum(1 for e in entries if e[6])
        unproductive_count = len(entries) - productive_count

        tag_counts = {}
        for entry in entries:
            tag = entry[5]
            tag_counts[tag] = tag_counts.get(tag, 0) + 1

        top_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        top_5_metrics = top_tags[:5]

        return {
            "pie_data": {"productive": productive_count, "unproductive": unproductive_count},
            "bar_data": top_tags,
            "radar_data": top_5_metrics
        }


class ActivityReview:
    """
    Handles preparation for the heatmap review screen.
    """

    def __init__(self):
        """
        Initializes the storage manager.
        """
        self.storage = ActivityStorage()

    def get_heatmap(self, month, year):
        """
        Prepares frequency dataset for the heatmap.

        Takes: month (str), year (str)
        Gives: dict mapping day (int) to frequency (int)
        """
        entries = self.storage.read_entries(month, year)
        heatmap_data = {}
        for entry in entries:
            day = int(entry[1].split("-")[2])
            heatmap_data[day] = heatmap_data.get(day, 0) + 1
        return heatmap_data

    def get_activity(self, date):
        """
        Retrieves activity logs for a specific date.

        Takes: date (str) 'YYYY-MM-DD'
        Gives: list of activity records
        """
        query = "SELECT * FROM activity WHERE date = ? ORDER BY start_time ASC"
        return self.storage.storage.read(query, (date,))
