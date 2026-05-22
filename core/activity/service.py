"""
File Name: service.py
Purpose: Logic and data management for the Activity Tracker feature.
"""

import json
import os
import subprocess
from core.shared.storage import StorageManager
from core.shared.configurator import ConfigManager


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
    Manages configuration settings for the activity module using ConfigManager.
    """

    def __init__(self):
        """
        Initializes the settings service with ConfigManager.

        Takes: None
        Gives: None
        """
        self.config_manager = ConfigManager()

    def _generate_systemd_files(self):
        """
        Regenerates the systemd service and timer files based on current config.

        Takes: None
        Gives: None
        """
        project_root = self.config_manager.read_value("system", "project_root")
        interval = self.config_manager.read_value("activity", "popup_interval_timer") or "30m"
        service_path = self.config_manager.read_value("activity", "service_path")
        timer_path = self.config_manager.read_value("activity", "timer_path")
        
        if project_root:
            zennify_sh = os.path.join(project_root, "tools/linux/zennify.sh")
            
            if service_path:
                service_content = f"""[Unit]
Description=Zennify Activity Tracking Service

[Service]
Type=oneshot
ExecStart={zennify_sh} --activity-popup
"""
                with open(service_path, "w") as f:
                    f.write(service_content)
            
            if timer_path:
                timer_content = f"""[Unit]
Description=Zennify Activity Tracking Timer

[Timer]
OnActiveSec={interval}
OnUnitActiveSec={interval}
Persistent=false

[Install]
WantedBy=timers.target
"""
                with open(timer_path, "w") as f:
                    f.write(timer_content)
            
            try:
                subprocess.run(["systemctl", "--user", "daemon-reload"], check=True)
            except subprocess.CalledProcessError:
                pass

    def toggle_service(self, enable):
        """
        Enables or disables the background systemd timer.

        Takes: enable (bool)
        Gives: None
        """
        state = "enable" if enable else "disable"
        action = "start" if enable else "stop"
        try:
            subprocess.run(["systemctl", "--user", state, "--now", "zennify-activity.timer"], check=True)
            self.config_manager.update_value("activity", "service_status", enable)
        except subprocess.CalledProcessError:
            pass

    def change_popup_interval_timer(self, new_interval):
        """
        Updates the popup interval timer and regenerates systemd files.

        Takes: new_interval (str)
        Gives: None
        """
        self.config_manager.update_value("activity", "popup_interval_timer", new_interval)
        self._generate_systemd_files()
        
        if self.config_manager.read_value("activity", "service_status"):
            try:
                subprocess.run(["systemctl", "--user", "restart", "zennify-activity.timer"], check=True)
            except subprocess.CalledProcessError:
                pass

    def change_popup_visible_timer(self, new_timer):
        """
        Updates the popup visible timer and regenerates systemd files.

        Takes: new_timer (str)
        Gives: None
        """
        self.config_manager.update_value("activity", "popup_visible_timer", new_timer)
        self._generate_systemd_files()

    def update_streak_data(self, streak, multiplier):
        """
        Updates the streak and multiplier in config.json.

        Takes: streak (int), multiplier (float)
        Gives: None
        """
        self.config_manager.update_value("activity", "streak", streak)
        self.config_manager.update_value("activity", "multiplier", multiplier)


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
