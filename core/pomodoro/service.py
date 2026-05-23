"""
File Name: service.py
Purpose: Logic and data management for the Pomodoro feature.
"""

import os
import json
import datetime
import math
from core.shared.storage import StorageManager
from core.shared.configurator import ConfigManager


class PomodoroStorage:
    """
    Handles database operations for pomodoro records.
    """

    def __init__(self):
        """
        Initializes the storage manager.
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


class PomodoroSettings:
    """
    Manages configuration settings for the pomodoro module using ConfigManager.
    """

    def __init__(self):
        """
        Initializes the configuration manager.
        """
        self.config_manager = ConfigManager()

    def read_config(self):
        """
        Reads all pomodoro configuration values.

        Takes: None
        Gives: dict
        """
        return {
            "work_time": self.config_manager.read_value("pomodoro", "work_time") or "60m",
            "short_break_time": self.config_manager.read_value("pomodoro", "short_break_time") or "5m",
            "long_break_time": self.config_manager.read_value("pomodoro", "long_break_time") or "15m",
            "long_break_interval": int(self.config_manager.read_value("pomodoro", "long_break_interval") or 4)
        }

    def change_preset(self, key, value):
        """
        Updates a specific pomodoro preset.

        Takes: key (str), value (any)
        Gives: None
        """
        self.config_manager.update_value("pomodoro", key, value)


class PomodoroStatistics:
    """
    Processes pomodoro data for overview visualizations.
    """

    def __init__(self):
        """
        Initializes the storage manager.
        """
        self.storage = PomodoroStorage()

    def give_overview(self, month=None, year=None):
        """
        Calculates analytics for the pomodoro dashboard.

        Takes: month (str), year (str)
        Gives: dict
        """
        all_sessions = self.storage.read_entries("SELECT date, start_time, duration_mins, phase FROM pomodoro")
        
        if not all_sessions:
            return {
                "total_zen_time": "0d 0h 0m",
                "avg_daily_focus": 0,
                "heatmap_24h": [0]*24,
                "heatmap_month": {},
                "dow_data": [0]*7,
                "session_dist": {"Deep Focus": 0, "Standard": 0, "Short Burst": 0},
                "trend_data": []
            }

        total_mins = sum(s[2] for s in all_sessions)
        active_days = len(set(s[0] for s in all_sessions))
        avg_focus = total_mins / active_days if active_days > 0 else 0

        # Total Zen Time string
        days = total_mins // (24 * 60)
        hours = (total_mins % (24 * 60)) // 60
        mins = total_mins % 60
        zen_time_str = f"{int(days)}d {int(hours)}h {int(mins)}m"

        # 24h Heatmap
        h24 = [0]*24
        for s in all_sessions:
            try:
                hour = int(s[1].split(":")[0])
                if 0 <= hour < 24:
                    h24[hour] += s[2]
            except (ValueError, IndexError):
                continue

        # Day of Week
        dow = [0]*7
        for s in all_sessions:
            try:
                d = datetime.datetime.strptime(s[0], "%Y-%m-%d").weekday()
                dow[d] += s[2]
            except ValueError:
                continue

        # Session Distribution
        dist = {"Deep Focus": 0, "Standard": 0, "Short Burst": 0}
        for s in all_sessions:
            if s[2] >= 50: dist["Deep Focus"] += 1
            elif s[2] >= 25: dist["Standard"] += 1
            else: dist["Short Burst"] += 1

        # Trend Analysis (Last 30 days)
        now = datetime.datetime.now()
        trend = []
        for i in range(29, -1, -1):
            day = (now - datetime.timedelta(days=i)).strftime("%Y-%m-%d")
            day_mins = sum(s[2] for s in all_sessions if s[0] == day)
            trend.append((day, day_mins))

        return {
            "total_zen_time": zen_time_str,
            "avg_daily_focus": round(avg_focus, 1),
            "heatmap_24h": h24,
            "dow_data": dow,
            "session_dist": dist,
            "trend_data": trend
        }


class PomodoroTimer:
    """
    Handles internal timer logic and state persistence.
    """

    def __init__(self):
        """
        Initializes the timer and loads persisted state if it exists.
        """
        self.settings = PomodoroSettings()
        self.storage = PomodoroStorage()
        
        # Derive data directory from config_path
        config_dir = os.path.dirname(self.settings.config_manager.config_path)
        self.state_path = os.path.join(config_dir, "pomodoro_state.json")
        
        self.state = self._load_state()

    def _load_state(self):
        """
        Loads the timer state from data/pomodoro_state.json.
        """
        if os.path.exists(self.state_path):
            try:
                with open(self.state_path, "r") as f:
                    return json.load(f)
            except Exception:
                pass
        
        return {
            "phase": "Work",
            "is_running": False,
            "remaining_seconds": self._parse_time(self.settings.read_config()["work_time"]),
            "completed_pomodoros": 0,
            "last_update": None
        }

    def _save_state(self):
        """
        Persists the current state to data/pomodoro_state.json.
        """
        os.makedirs(os.path.dirname(self.state_path), exist_ok=True)
        with open(self.state_path, "w") as f:
            json.dump(self.state, f, indent=4)

    def _parse_time(self, time_str):
        """
        Parses time strings like '60m' or '5M' into seconds.
        """
        try:
            val = int(time_str[:-1])
            return val * 60
        except (ValueError, IndexError):
            return 25 * 60

    def get_current_state(self):
        """
        Returns the current timer state, adjusting for elapsed time if running.
        """
        if self.state["is_running"] and self.state["last_update"]:
            now = datetime.datetime.now().timestamp()
            elapsed = int(now - self.state["last_update"])
            self.state["remaining_seconds"] = max(0, self.state["remaining_seconds"] - elapsed)
            self.state["last_update"] = now
            if self.state["remaining_seconds"] == 0:
                self.state["is_running"] = False
            self._save_state()
        return self.state

    def start(self):
        """
        Starts or resumes the timer.
        """
        self.state["is_running"] = True
        self.state["last_update"] = datetime.datetime.now().timestamp()
        self._save_state()

    def pause(self):
        """
        Pauses the timer.
        """
        self.get_current_state() # Update remaining seconds
        self.state["is_running"] = False
        self.state["last_update"] = None
        self._save_state()

    def stop(self):
        """
        Stops and resets the timer to the current phase's default time.
        """
        config = self.settings.read_config()
        self.state["is_running"] = False
        self.state["last_update"] = None
        if self.state["phase"] == "Work":
            self.state["remaining_seconds"] = self._parse_time(config["work_time"])
        elif self.state["phase"] == "Short Break":
            self.state["remaining_seconds"] = self._parse_time(config["short_break_time"])
        else:
            self.state["remaining_seconds"] = self._parse_time(config["long_break_time"])
        self._save_state()

    def change_phase(self):
        """
        Advances to the next phase based on pomodoro rules.
        """
        config = self.settings.read_config()
        if self.state["phase"] == "Work":
            self.state["completed_pomodoros"] += 1
            if self.state["completed_pomodoros"] % config["long_break_interval"] == 0:
                self.state["phase"] = "Long Break"
                self.state["remaining_seconds"] = self._parse_time(config["long_break_time"])
            else:
                self.state["phase"] = "Short Break"
                self.state["remaining_seconds"] = self._parse_time(config["short_break_time"])
        else:
            self.state["phase"] = "Work"
            self.state["remaining_seconds"] = self._parse_time(config["work_time"])
        
        self.state["is_running"] = False
        self.state["last_update"] = None
        self._save_state()

    def mark_complete(self, duration_mins):
        """
        Logs a completed phase to the database.
        """
        now = datetime.datetime.now()
        start_time = (now - datetime.timedelta(minutes=duration_mins)).strftime("%H:%M")
        self.storage.write_entries(
            "INSERT INTO pomodoro (date, start_time, end_time, duration_mins, phase) VALUES (?, ?, ?, ?, ?)",
            (now.strftime("%Y-%m-%d"), start_time, now.strftime("%H:%M"), duration_mins, self.state["phase"])
        )

    def restart(self):
        """
        Hard resets the timer to the beginning of a new Pomodoro cycle.
        """
        config = self.settings.read_config()
        self.state["phase"] = "Work"
        self.state["is_running"] = False
        self.state["last_update"] = None
        self.state["completed_pomodoros"] = 0
        self.state["remaining_seconds"] = self._parse_time(config["work_time"])
        self._save_state()
