"""
File Name: service.py
Purpose: Logic and data management for the Todos feature.
"""

import datetime
import statistics
import io
import base64
import matplotlib
import matplotlib.pyplot as plt
from core.shared.storage import StorageManager
from core.shared.configurator import ConfigManager
from core.shared.wallet import WalletManager

matplotlib.use("agg")

class TodoSettings:
    """
    Manages configuration settings for the todo module using ConfigManager.
    """

    def __init__(self):
        """
        Initializes the configuration manager.
        """
        self.config_manager = ConfigManager()

    def read_config(self):
        """
        Reads all todo configuration values.

        Takes: None
        Gives: dict
        """
        return {
            "max_tasks": self.config_manager.read_value("todo", "max_tasks") or 5,
            "streak": self.config_manager.read_value("todo", "streak") or 0,
            "multiplier": self.config_manager.read_value("todo", "multiplier") or 1.0
        }

    def change_max_tasks(self, value):
        """
        Updates the running task limit.

        Takes: value (int)
        Gives: None
        """
        self.config_manager.update_value("todo", "max_tasks", int(value))


    def update_streak_data(self, streak, multiplier):
        """
        Updates the streak and multiplier in config.json.

        Takes: streak (int), multiplier (float)
        Gives: None
        """
        self.config_manager.update_value("todo", "streak", streak)
        self.config_manager.update_value("todo", "multiplier", multiplier)

class TodoStatistics:
    """
    Processes data for the overview dashboard using hardcore analytics.
    """

    def __init__(self):
        """
        Initializes the statistics service.
        """
        self.storage = StorageManager()
        self.settings = TodoSettings()

    def _fig_to_base64(self, fig, bg_color):
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

    def give_overview(self):
        """
        Calculates complex metrics for the overview dashboard.

        Takes:
          None.

        Gives:
          dict: A dictionary containing streak, multiplier and overview_data list.
        """
        all_tasks = self.storage.read("SELECT creation_date, deadline, status, completion_time FROM todo")
        config = self.settings.read_config()
        
        comp_score = 0
        focus_score = 0
        consistency_std = 0
        daily_counts = [0] * 30
        scatter_points = []
        total = len(all_tasks)
        comp_count = 0

        if all_tasks:
            completed = [t for t in all_tasks if t[2] == "Completed"]
            comp_count = len(completed)
            comp_score = (comp_count / total * 100) if total > 0 else 0
            
            focus_points = []
            for t in completed:
                try:
                    start = datetime.datetime.fromisoformat(t[0]).astimezone()
                    ddl = datetime.datetime.fromisoformat(t[1]).astimezone()
                    end = datetime.datetime.fromisoformat(t[3]).astimezone()
                    
                    broadness = (ddl - start).total_seconds() / 3600
                    speed = (end - start).total_seconds() / 3600
                    scatter_points.append((broadness, speed))
                    
                    if broadness > 0:
                        ratio = speed / broadness
                        score = max(0, 100 * (1 - ratio))
                        focus_points.append(score)
                except (ValueError, TypeError):
                    continue

            focus_score = statistics.mean(focus_points) if focus_points else 0
            
            now = datetime.datetime.now()
            daily_counts = []
            for i in range(30):
                day = (now - datetime.timedelta(days=i)).strftime("%Y-%m-%d")
                count = sum(1 for t in completed if t[3].startswith(day))
                daily_counts.append(count)
            
            consistency_std = statistics.stdev(daily_counts) if len(daily_counts) > 1 else 0

        bg_color = "#111418"
        plt.rcParams.update({
            "text.color": "white",
            "axes.labelcolor": "white",
            "xtick.color": "white",
            "ytick.color": "white",
            "axes.edgecolor": "white"
        })

        fig1, ax1 = plt.subplots(figsize=(7, 4))
        ax1.set_facecolor(bg_color)
        ax1.plot(daily_counts[::-1], color="#42A5F5", marker="o", linewidth=2)
        ax1.set_title("Consistency Trend (Last 30 Days)", color="white")
        chart1_base64 = self._fig_to_base64(fig1, bg_color)

        fig2, ax2 = plt.subplots(figsize=(7, 4))
        ax2.set_facecolor(bg_color)
        if scatter_points:
            x, y = zip(*scatter_points)
            ax2.scatter(x, y, color="#FFCA28", alpha=0.6)
            max_val = max(max(x), max(y))
            ax2.plot([0, max_val], [0, max_val], color="red", linestyle="--", alpha=0.5)
        else:
            ax2.text(0.5, 0.5, "No Data", ha='center', va='center', color="white")
        ax2.set_xlabel("Vastness (Hours)")
        ax2.set_ylabel("Speed to Finish (Hours)")
        chart2_base64 = self._fig_to_base64(fig2, bg_color)

        overview_data = [
            {
                "title": "Completion Score",
                "type": "text",
                "value": f"{round(comp_score, 1)}%",
                "explanation": "This is the percentage of your completed tasks out of total tasks.",
                "insight": f"Out of {total} total tasks, you completed {comp_count}."
            },
            {
                "title": "Focus Score",
                "type": "text",
                "value": f"{round(focus_score, 1)} / 100",
                "explanation": "Score based on how quickly you finish tasks before their deadlines. Higher is better.",
                "insight": "A higher focus score means less procrastination."
            },
            {
                "title": "Consistency Trend",
                "type": "chart",
                "image_base64": chart1_base64,
                "explanation": "This chart shows your task completion volume over the last 30 days. It helps identify if you're a steady worker or a rollercoaster performer.",
                "insight": f"Your completion stability (Standard Deviation) is {round(consistency_std, 2)}."
            },
            {
                "title": "Lead Time vs Urgency",
                "type": "chart",
                "image_base64": chart2_base64,
                "explanation": "X-axis represents 'Broadness' (deadline window), Y-axis is 'Speed to Finish'. Dots near the red line are last-minute completions. Proactive finishes stay far below the line.",
                "insight": "Try to keep your data points in the 'Proactive Zone' far below the diagonal line."
            }
        ]
        
        return {
            "streak": config["streak"],
            "multiplier": config["multiplier"],
            "overview_data": overview_data
        }

class TodoTasks:
    """
    Handles task lifecycle management and hardcore deadline enforcement.
    """

    def __init__(self):
        """
        Initializes the tasks service and runs deadline enforcement.
        """
        self.storage = StorageManager()
        self.settings = TodoSettings()
        self.wallet = WalletManager()
        self.enforce_deadlines()

    def enforce_deadlines(self):
        """
        Hardcore mode: Marks past-due tasks as failed automatically.
        Called on startup.
        """
        now = datetime.datetime.now().astimezone()
        running_tasks = self.storage.read("SELECT task_id, task_name, deadline FROM todo WHERE status = 'Running'")
        for task in running_tasks:
            tid, name, ddl_str = task
            try:
                deadline = datetime.datetime.fromisoformat(ddl_str).astimezone()
                if now > deadline:
                    self.mark_task(tid, "Failed")
            except (ValueError, TypeError) as e:
                print(e)
                continue

    def add_task(self, name, deadline_str):
        """
        Adds a new task if under the running task limit.

        Takes: name (str), deadline_str (str)
        Gives: tuple (bool, str)
        """
        config = self.settings.read_config()
        running_count = len(self.list_running_tasks())
        
        if running_count >= config["max_tasks"]:
            return False, f"Task limit reached ({config['max_tasks']})"
            
        now = datetime.datetime.now().isoformat()
        self.storage.write("INSERT INTO todo (task_name, creation_date, deadline, status) VALUES (?, ?, ?, ?)", (name, now, deadline_str, "Running"))
        return True, "Task added successfully"

    def mark_task(self, task_id, status):
        """
        Finalizes a task as Completed or Failed and applies rewards/penalties.

        Takes: task_id (int), status (str)
        Gives: None
        """
        now = datetime.datetime.now().isoformat()
        config = self.settings.read_config()
        streak = config["streak"]
        multiplier = config["multiplier"]

        if status == "Completed":
            reward = round(5 * multiplier, 1)
            self.wallet.earn_coins(reward)
            streak += 1
            multiplier = min(2.0, multiplier + 0.1)
            retribution = reward
        else:
            self.wallet.earn_coins(-2)
            streak = 0
            multiplier = 1.0
            retribution = -2
            
        self.storage.write("UPDATE todo SET status = ?, completion_time = ?, retribution = ? WHERE task_id = ?", (status, now, retribution, task_id))
        self.settings.update_streak_data(streak, round(multiplier, 1))

    def list_running_tasks(self):
        """
        Retrieves current active tasks.

        Takes: None
        Gives: list of records
        """
        return self.storage.read("SELECT task_id, task_name, deadline FROM todo WHERE status = 'Running' ORDER BY deadline ASC")

    def list_finalized_tasks(self, month, year):
        """
        Retrieves tasks finalized (Completed or Failed) in a specific period for the heatmap.

        Takes: month (str), year (str)
        Gives: list of records
        """
        pattern = f"{year}-{month}-%"
        return self.storage.read("SELECT * FROM todo WHERE completion_time LIKE ? AND status IN ('Completed', 'Failed')", (pattern,))
