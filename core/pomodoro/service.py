"""
File Name: service.py
Purpose: Logic and data management for the Pomodoro feature.
"""

import os
import json
import datetime
import math
import io
import base64
import matplotlib
import matplotlib.pyplot as plt
from core.shared.storage import StorageManager
from core.shared.configurator import ConfigManager

matplotlib.use("agg")


class PomodoroSettings:
    """
    Provides a high-level interface for managing Pomodoro configuration presets.
    Handles reading and updating work, short break, and long break durations.
    """

    def __init__(self):
        """
        Initializes the configuration manager instance for the settings service.

        Takes:
          None.

        Gives:
          None.
        """
        self.config_manager = ConfigManager()

    def get_preset(self):
        """
        Retrieves all currently configured Pomodoro presets from the storage.

        Takes:
          None.

        Gives:
          dict: A dictionary containing work_time, short_break_time, long_break_time, and long_break_interval.
        """
        return {
            "work_time": self.config_manager.read_value("pomodoro", "work_time") or "60m",
            "short_break_time": self.config_manager.read_value("pomodoro", "short_break_time") or "5m",
            "long_break_time": self.config_manager.read_value("pomodoro", "long_break_time") or "15m",
            "long_break_interval": int(self.config_manager.read_value("pomodoro", "long_break_interval") or 4)
        }

    def change_preset(self, work_time, short_break_time, long_break_time, long_break_interval):
        """
        Updates the Pomodoro presets with new values provided by the user.

        Takes:
          work_time (str): The duration of a work session (e.g., '25m').
          short_break_time (str): The duration of a short break (e.g., '5m').
          long_break_time (str): The duration of a long break (e.g., '15m').
          long_break_interval (int): The number of work sessions before a long break.

        Gives:
          None.
        """
        self.config_manager.update_value("pomodoro", "work_time", work_time)
        self.config_manager.update_value("pomodoro", "short_break_time", short_break_time)
        self.config_manager.update_value("pomodoro", "long_break_time", long_break_time)
        self.config_manager.update_value("pomodoro", "long_break_interval", long_break_interval)


class PomodoroStatistics:
    """
    Handles the aggregation and visualization of Pomodoro session data.
    Generates statistical reports and charts for user productivity analysis.
    """

    def __init__(self):
        """
        Initializes the statistics service with a storage manager instance.

        Takes:
          None.

        Gives:
          None.
        """
        self.storage = StorageManager()

    def _fig_to_base64(self, fig, bg_color) :
        """
        Converts a Matplotlib figure into a base64 encoded PNG string.

        Takes:
          fig (plt.Figure): The Matplotlib figure object to be converted.
          bg_color (str): The background color to apply to the figure.

        Gives:
          str: A base64 encoded PNG image string suitable for Flet display.
        """
        buf = io.BytesIO()
        fig.tight_layout(pad=1.5)
        fig.savefig(buf, format="png", bbox_inches="tight", facecolor=bg_color, dpi=100)
        plt.close(fig)
        return base64.b64encode(buf.getvalue()).decode("utf-8")

    def give_overview(self, month=None, year=None):
        """
        Generates a comprehensive statistical overview of Pomodoro usage.

        Takes:
          month (str): Optional month filter in 'mm' format.
          year (str): Optional year filter in 'yyyy' format.

        Gives:
          list: A list of standardized metric dictionaries containing charts and summaries.
        """
        all_sessions = self.storage.read("SELECT date, start_time, duration_mins, phase FROM pomodoro")
        
        if not all_sessions:
            return []

        total_mins = sum(s[2] for s in all_sessions)
        active_days = len(set(s[0] for s in all_sessions))
        avg_focus = total_mins / active_days if active_days > 0 else 0

        days = total_mins // (24 * 60)
        hours = (total_mins % (24 * 60)) // 60
        mins = total_mins % 60
        zen_time_str = f"{int(days)}d {int(hours)}h {int(mins)}m"

        h24 = [0]*24
        for s in all_sessions:
            try:
                hour = int(s[1].split(":")[0])
                if 0 <= hour < 24:
                    h24[hour] += s[2]
            except (ValueError, IndexError):
                continue

        dow = [0]*7
        for s in all_sessions:
            try:
                d = datetime.datetime.strptime(s[0], "%Y-%m-%d").weekday()
                dow[d] += s[2]
            except ValueError:
                continue

        dist = {"Deep Focus": 0, "Standard": 0, "Short Burst": 0}
        for s in all_sessions:
            if s[2] >= 50: dist["Deep Focus"] += 1
            elif s[2] >= 25: dist["Standard"] += 1
            else: dist["Short Burst"] += 1

        now = datetime.datetime.now()
        trend = []
        for i in range(29, -1, -1):
            day = (now - datetime.timedelta(days=i)).strftime("%Y-%m-%d")
            day_mins = sum(s[2] for s in all_sessions if s[0] == day)
            trend.append((day, day_mins))

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
        days_labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        ax1.bar(days_labels, dow, color="#42A5F5")
        chart1_base64 = self._fig_to_base64(fig1, bg_color)

        fig2, ax2 = plt.subplots(figsize=(7, 4))
        ax2.set_facecolor(bg_color)
        raw_labels = list(dist.keys())
        raw_values = list(dist.values())
        labels = [l for l, v in zip(raw_labels, raw_values) if v > 0]
        values = [v for v in raw_values if v > 0]
        if sum(values) > 0:
            all_colors = ["#66BB6A", "#FFA726", "#EF5350"]
            colors = [c for c, v in zip(all_colors, raw_values) if v > 0]
            ax2.pie(values, labels=labels, autopct='%1.1f%%', colors=colors, textprops={'color':"w"})
        else:
            ax2.text(0.5, 0.5, "No Data", ha='center', va='center')
        chart2_base64 = self._fig_to_base64(fig2, bg_color)

        fig3, ax3 = plt.subplots(figsize=(7, 4))
        ax3.set_facecolor(bg_color)
        if trend:
            dates, mins_list = zip(*trend)
            short_dates = [d[-5:] for d in dates]
            ax3.plot(short_dates, mins_list, color="#FFCA28", marker="o", linewidth=2)
            for i, t in enumerate(ax3.get_xticklabels()):
                if i % 5 != 0: t.set_visible(False)
        else:
            ax3.text(0.5, 0.5, "No Data", ha='center', va='center')
        chart3_base64 = self._fig_to_base64(fig3, bg_color)

        fig4, ax4 = plt.subplots(figsize=(7, 4))
        ax4.set_facecolor(bg_color)
        hours_labels = [str(i) for i in range(24)]
        ax4.bar(hours_labels, h24, color="#26C6DA")
        ax4.set_xticks(range(0, 24, 2))
        chart4_base64 = self._fig_to_base64(fig4, bg_color)

        return [
            {
                "type": "text",
                "title": "Total Zen Time",
                "value": zen_time_str,
                "explanation": "Accumulated focus time across all your sessions. It represents the total amount of deep work you have performed.",
                "insight": "Great progress! Your total zen time shows consistent dedication to your tasks."
            },
            {
                "type": "text",
                "title": "Average Daily Focus",
                "value": f"{round(avg_focus, 1)}m",
                "explanation": "Calculates the average number of minutes you spend focusing each day you log activity. It helps you track your daily rhythm.",
                "insight": f"You average {round(avg_focus, 1)} minutes of focus per day. Try to increase this gradually for better productivity."
            },
            {
                "type": "chart",
                "title": "24-Hour Focus Distribution",
                "image_base64": chart4_base64,
                "explanation": "Visualizes which hours of the day you are most active. This helps identify your peak performance periods.",
                "insight": "Use this data to schedule your most demanding tasks during your peak focus hours."
            },
            {
                "type": "chart",
                "title": "Day-of-Week Comparison",
                "image_base64": chart1_base64,
                "explanation": "Compares your total focus time across different days of the week. Helps identify your most and least productive days.",
                "insight": "Identify your 'Warrior' days and try to replicate that focus on days where you typically lag behind."
            },
            {
                "type": "chart",
                "title": "Session Distribution",
                "image_base64": chart2_base64,
                "explanation": "Categorizes your sessions by length: Deep Focus (>50m), Standard (~25m), and Short Bursts. More Deep Focus indicates better flow state.",
                "insight": "Aim for a higher percentage of 'Deep Focus' sessions to tackle complex projects effectively."
            },
            {
                "type": "chart",
                "title": "Focus Trend (Last 30 Days)",
                "image_base64": chart3_base64,
                "explanation": "Tracks your daily focus volume over time. Useful for spotting burnout or growing productivity habits.",
                "insight": "Watch for downward trends which might signal a need for more rest or a change in environment."
            }
        ]


class PomodoroTimer:
    """
    Manages the active state and lifecycle of the Pomodoro timer.
    Handles starting, pausing, stopping, and transitioning between work and break phases.
    """

    def __init__(self):
        """
        Initializes the timer service and restores the previous state from persistence.

        Takes:
          None.

        Gives:
          None.
        """
        self.settings = PomodoroSettings()
        self.storage = StorageManager()

        config_dir = os.path.dirname(self.settings.config_manager.config_path)
        self.state_path = os.path.join(config_dir, "pomodoro_state.json")
        
        self.state = self._load_state()

    def _load_state(self):
        """
        Loads the persisted timer state from the local JSON storage file.

        Takes:
          None.

        Gives:
          dict: The restored timer state or a default state if no file exists.
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
            "remaining_seconds": self._parse_time(self.settings.get_preset()["work_time"]),
            "completed_pomodoros": 0,
            "last_update": None
        }

    def _save_state(self):
        """
        Persists the current timer state to a local JSON storage file.

        Takes:
          None.

        Gives:
          None.
        """
        os.makedirs(os.path.dirname(self.state_path), exist_ok=True)
        with open(self.state_path, "w") as f:
            json.dump(self.state, f, indent=4)

    def _parse_time(self, time_str):
        """
        Converts a human-readable time string into a duration in seconds.

        Takes:
          time_str (str): The time string to parse (e.g., '60m').

        Gives:
          int: The equivalent duration in seconds.
        """
        try:
            val = int(time_str[:-1])
            return val * 60
        except (ValueError, IndexError):
            return 25 * 60

    def get_current_state(self):
        """
        Calculates and returns the current state of the timer, accounting for elapsed time.

        Takes:
          None.

        Gives:
          dict: The updated timer state dictionary.
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
        Begins or resumes the countdown of the Pomodoro timer.

        Takes:
          None.

        Gives:
          None.
        """
        self.state["is_running"] = True
        self.state["last_update"] = datetime.datetime.now().timestamp()
        self._save_state()

    def pause(self):
        """
        Suspends the active Pomodoro timer countdown.

        Takes:
          None.

        Gives:
          None.
        """
        self.get_current_state()
        self.state["is_running"] = False
        self.state["last_update"] = None
        self._save_state()

    def stop(self):
        """
        Interrupts the current session and resets the timer to the phase's initial duration.

        Takes:
          None.

        Gives:
          None.
        """
        config = self.settings.get_preset()
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
        Transitions the timer to the next logical phase (Work, Short Break, or Long Break).

        Takes:
          None.

        Gives:
          None.
        """
        config = self.settings.get_preset()
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
        Records a completed Pomodoro phase into the activity database.

        Takes:
          duration_mins (int): The number of focused minutes to log.

        Gives:
          None.
        """
        now = datetime.datetime.now()
        start_time = (now - datetime.timedelta(minutes=duration_mins)).strftime("%H:%M")
        self.storage.write(
            "INSERT INTO pomodoro (date, start_time, end_time, duration_mins, phase) VALUES (?, ?, ?, ?, ?)",
            (now.strftime("%Y-%m-%d"), start_time, now.strftime("%H:%M"), duration_mins, self.state["phase"])
        )

    def restart(self):
        """
        Performs a hard reset of the timer cycle to the beginning of a work session.

        Takes:
          None.

        Gives:
          None.
        """
        config = self.settings.get_preset()
        self.state["phase"] = "Work"
        self.state["is_running"] = False
        self.state["last_update"] = None
        self.state["completed_pomodoros"] = 0
        self.state["remaining_seconds"] = self._parse_time(config["work_time"])
        self._save_state()
