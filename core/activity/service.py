"""
File Name: service.py
Purpose: Logic and data management for the Activity Tracker feature.
"""

import json
import os
import subprocess
import io
import base64
import math
import matplotlib
import matplotlib.pyplot as plt
from core.shared.storage import StorageManager
from core.shared.configurator import ConfigManager

matplotlib.use("agg")

class ActivityOverlay:
    """
    Handles data retrieval and persistence for the activity logging popup.
    """

    def __init__(self):
        """
        Initializes the storage manager for the activity overlay.

        Takes:
            None: Uses the default StorageManager initialization.

        Gives:
            None: Initializes the 'storage' attribute.
        """
        self.storage = StorageManager()

    def get_recent_tags(self):
        """
        Retrieves unique tags previously used in activities for selection in the popup.

        Takes:
            None: Queries the 'activity' table for distinct tags.

        Gives:
            list: A list of unique strings representing previously used tags.
        """
        query = "SELECT DISTINCT tag FROM activity ORDER BY tag ASC"
        rows = self.storage.read(query)
        return [row[0] for row in rows]

    def get_last_entry(self):
        """
        Retrieves the most recent activity entry to calculate streaks and multipliers.

        Takes:
            None: Queries the 'activity' table for the latest record.

        Gives:
            tuple: The latest activity record, or None if no records exist.
        """
        query = "SELECT * FROM activity ORDER BY session_id DESC LIMIT 1"
        rows = self.storage.read(query)
        return rows[0] if rows else None

    def write_entry(self, date, start_time, end_time, description, tag, is_productive, retribution):
        """
        Writes a new activity entry to the database.

        Takes:
            date (str): The date of the activity (YYYY-MM-DD).
            start_time (str): The start time of the session (HH:MM).
            end_time (str): The end time of the session (HH:MM).
            description (str): A brief description of the activity.
            tag (str): The category tag for the activity.
            is_productive (bool): Whether the session was productive.
            retribution (int): The coin reward or penalty for the session.

        Gives:
            None: Commits the new entry to the database.
        """
        query = """
        INSERT INTO activity (date, start_time, end_time, description, tag, is_productive, retribution)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        self.storage.write(query, (date, start_time, end_time, description, tag, is_productive, retribution))


class ActivitySettings:
    """
    Manages configuration settings and systemd integration for the activity module.
    """

    def __init__(self):
        """
        Initializes the settings service with a configuration manager.

        Takes:
            None: Uses the default ConfigManager initialization.

        Gives:
            None: Initializes the 'config_manager' attribute.
        """
        self.config_manager = ConfigManager()

    def _generate_windows_task(self):
        """
        Regenerates the Windows Task Scheduler entry based on current configuration.

        Takes:
            None: Reads values from the configuration manager.

        Gives:
            None: Executes schtasks commands to update the task.
        """
        project_root = self.config_manager.read_value("system", "project_root")
        interval = self.config_manager.read_value("activity", "popup_interval_timer") or "30m"
        task_name = "ZennifyActivityTask"
        
        if project_root:
            zennify_bat = os.path.join(project_root, "tools", "windows", "zennify.bat")
            
            if interval.endswith("m"):
                sc = "minute"
                mo = interval.replace("m", "")
            elif interval.endswith("h"):
                sc = "hourly"
                mo = interval.replace("h", "")
            else:
                sc = "minute"
                mo = "30"

            try:
                create_cmd = ["schtasks", "/create", "/tn", task_name, "/tr", f'"{zennify_bat}" --activity-popup', "/sc", sc, "/mo", mo, "/f"]
                subprocess.run(create_cmd, check=True, capture_output=True)
                
                if not self.config_manager.read_value("activity", "service_status"):
                    subprocess.run(["schtasks", "/change", "/tn", task_name, "/disable"], check=True, capture_output=True)
            except subprocess.CalledProcessError:
                pass

    def _generate_systemd_files(self):
        """
        Regenerates the systemd service and timer files based on current configuration.

        Takes:
            None: Reads values from the configuration manager.

        Gives:
            None: Writes files to the systemd user configuration directory.
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
        Enables or disables the background timer for activity logging.

        Takes:
            enable (bool): True to enable and start the service, False to disable and stop it.

        Gives:
            None: Executes OS-specific commands and updates configuration.
        """
        state = "enable" if enable else "disable"
        if os.name == "nt":
            try:
                subprocess.run(["schtasks", "/change", "/tn", "ZennifyActivityTask", f"/{state}"], check=True, capture_output=True)
                self.config_manager.update_value("activity", "service_status", enable)
            except subprocess.CalledProcessError:
                pass
        else:
            try:
                subprocess.run(["systemctl", "--user", state, "--now", "zennify-activity.timer"], check=True)
                self.config_manager.update_value("activity", "service_status", enable)
            except subprocess.CalledProcessError:
                pass

    def change_popup_interval_timer(self, new_interval):
        """
        Updates the popup interval timer and regenerates associated background tasks.

        Takes:
            new_interval (str): The new timer interval (e.g., '1h', '45m').

        Gives:
            None: Updates configuration, regenerates files/tasks, and restarts if necessary.
        """
        self.config_manager.update_value("activity", "popup_interval_timer", new_interval)
        
        if os.name == "nt":
            self._generate_windows_task()
        else:
            self._generate_systemd_files()
            if self.config_manager.read_value("activity", "service_status"):
                try:
                    subprocess.run(["systemctl", "--user", "restart", "zennify-activity.timer"], check=True)
                except subprocess.CalledProcessError:
                    pass

    def change_popup_visible_timer(self, new_timer):
        """
        Updates the minimum visible time for the activity popup.

        Takes:
            new_timer (str): The new visibility duration (e.g., '2m', '5m').

        Gives:
            None: Updates the configuration value.
        """
        self.config_manager.update_value("activity", "popup_visible_timer", new_timer)

    def get_service_details(self):
        """
        Retrieves current systemd service configuration paths and status.

        Takes:
            None: Reads values from the configuration manager.

        Gives:
            list: A list containing [service_path (str), timer_path (str), service_status (bool)].
        """
        service_path = self.config_manager.read_value("activity", "service_path")
        timer_path = self.config_manager.read_value("activity", "timer_path")
        service_status = self.config_manager.read_value("activity", "service_status")
        return [service_path, timer_path, service_status]

    def get_timer_details(self):
        """
        Retrieves current timer settings for the activity popup.

        Takes:
            None: Reads values from the configuration manager.

        Gives:
            list: A list containing [popup_interval_timer (str), popup_visible_timer (str)].
        """
        popup_interval_timer = self.config_manager.read_value("activity", "popup_interval_timer")
        popup_visible_timer = self.config_manager.read_value("activity", "popup_visible_timer")
        return [popup_interval_timer, popup_visible_timer]

    def get_streak_data(self):
        """
        Retrieves current user streak and multiplier data.

        Takes:
            None: Reads values from the configuration manager.

        Gives:
            list: A list containing [streak (int), multiplier (float)].
        """
        streak = self.config_manager.read_value("activity", "streak")
        multiplier = self.config_manager.read_value("activity", "multiplier")
        return [streak, multiplier]

    def update_streak_data(self, streak, multiplier):
        """
        Updates the user's activity streak and reward multiplier in the configuration.

        Takes:
            streak (int): The current consecutive productive sessions count.
            multiplier (float): The current reward multiplier based on productivity.

        Gives:
            None: Persists the new values to the configuration file.
        """
        self.config_manager.update_value("activity", "streak", streak)
        self.config_manager.update_value("activity", "multiplier", multiplier)


class ActivityStatistics:
    """
    Processes and aggregates activity data for visualization on the overview screen.
    """

    def __init__(self):
        """
        Initializes the statistics service with an activity storage manager.

        Takes:
            None: Initializes an internal StorageManager instance.

        Gives:
            None: Prepares the service for data processing.
        """
        self.storage = StorageManager()

    def _fig_to_base64(self, fig, bg_color):
        """
        Converts a Matplotlib figure into a base64 encoded string for Flet display.

        Takes:
            fig (plt.Figure): The Matplotlib figure object to convert.
            bg_color (str): The background color to apply to the saved figure.

        Gives:
            str: A base64 encoded PNG image string.
        """
        buf = io.BytesIO()
        fig.tight_layout(pad=1.5)
        fig.savefig(buf, format="png", bbox_inches="tight", facecolor=bg_color, dpi=100)
        plt.close(fig)
        return base64.b64encode(buf.getvalue()).decode("utf-8")

    def give_overview(self):
        """
        Generates aggregated statistics and pre-rendered charts for the overview screen.

        Takes:
            None: Analyzes all records in the activity table.

        Gives:
            list: A list of dictionaries containing chart titles, images, explanations, and insights.
        """
        query = "SELECT * FROM activity ORDER BY date ASC, start_time ASC"
        entries = self.storage.read(query)

        productive_count = sum(1 for e in entries if e[6])
        unproductive_count = len(entries) - productive_count

        tag_counts = {}
        for entry in entries:
            tag = entry[5]
            tag_counts[tag] = tag_counts.get(tag, 0) + 1

        top_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        top_5_metrics = top_tags[:5]

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
        total = productive_count + unproductive_count
        if total > 0:
            ax1.pie([productive_count, unproductive_count], labels=["Productive", "Unproductive"], autopct='%1.1f%%', colors=["#66BB6A", "#EF5350"], textprops={'color':"w"})
            prod_pc = round((productive_count / total * 100), 1)
        else:
            ax1.text(0.5, 0.5, "No Data", ha='center', va='center', color="white")
            prod_pc = 0
        chart1_base64 = self._fig_to_base64(fig1, bg_color)

        fig2 = plt.figure(figsize=(7, 4))
        fig2.patch.set_facecolor(bg_color)
        if len(top_5_metrics) >= 3:
            ax2 = fig2.add_subplot(111, polar=True)
            ax2.set_facecolor(bg_color)
            labels = [item[0] for item in top_5_metrics]
            values = [item[1] for item in top_5_metrics]
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
        chart2_base64 = self._fig_to_base64(fig2, bg_color)

        fig3, ax3 = plt.subplots(figsize=(7, 4))
        ax3.set_facecolor(bg_color)
        if top_tags:
            labels = [item[0] for item in top_tags]
            counts = [item[1] for item in top_tags]
            ax3.bar(labels, counts, color="#26C6DA")
            ax3.tick_params(axis='x', rotation=45)
        else:
            ax3.text(0.5, 0.5, "No Data", ha='center', va='center', color="white")
        chart3_base64 = self._fig_to_base64(fig3, bg_color)

        return [
            {
                "title": "Productivity Ratio",
                "image_base64": chart1_base64,
                "explanation": "This chart shows the balance between your productive and unproductive sessions. It gives a quick glance at how effectively you're spending your logged time.",
                "insight": f"Your productivity ratio overall is {prod_pc}%."
            },
            {
                "title": "Activity Mix (Top 5)",
                "image_base64": chart2_base64,
                "explanation": "The radar chart displays your top 5 activities, forming a 'shape' of your habits. A well-rounded shape indicates varied activities, while spikes show intense focus on specific areas.",
                "insight": f"Your dominant activity is '{top_activity}'."
            },
            {
                "title": "Detailed Tag Frequency",
                "image_base64": chart3_base64,
                "explanation": "This bar chart provides a detailed breakdown of all your activity tags by their frequency of use, highlighting where your time is being invested the most.",
                "insight": f"You have tracked {len(top_tags)} different activities overall."
            }
        ]


class ActivityReview:
    """
    Prepares activity data for the heatmap and daily review screens.
    """

    def __init__(self):
        """
        Initializes the review service with a storage manager.

        Takes:
            None: Initializes an internal StorageManager instance.

        Gives:
            None: Prepares the service for data retrieval.
        """
        self.storage = StorageManager()

    def get_heatmap(self, month, year):
        """
        Calculates activity frequency per day for the heatmap visualization.

        Takes:
            month (str): The month to analyze.
            year (str): The year to analyze.

        Gives:
            dict: A dictionary mapping day numbers (int) to session counts (int).
        """
        pattern = f"{year}-{month}-%"
        query = "SELECT * FROM activity WHERE date LIKE ? ORDER BY date ASC, start_time ASC"
        entries = self.storage.read(query, (pattern,))
        heatmap_data = {}
        for entry in entries:
            day = int(entry[1].split("-")[2])
            heatmap_data[day] = heatmap_data.get(day, 0) + 1
        return heatmap_data

    def get_activity(self, date):
        """
        Retrieves all activity logs for a specific calendar date.

        Takes:
            date (str): The date in 'YYYY-MM-DD' format.

        Gives:
            list: A list of activity records for the given date, ordered by start time.
        """
        query = "SELECT * FROM activity WHERE date = ? ORDER BY start_time ASC"
        return self.storage.read(query, (date,))
