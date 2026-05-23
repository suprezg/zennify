"""
File Name: service.py
Purpose: Logic and data management for the Todos feature.
"""

import datetime
import statistics
from core.shared.storage import StorageManager
from core.shared.configurator import ConfigManager
from core.shared.wallet import WalletManager


class TodoStorage:
    """
    Handles database operations for todo records.
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


class TodoTasks:
    """
    Handles task lifecycle management and hardcore deadline enforcement.
    """

    def __init__(self):
        """
        Initializes the tasks service and runs deadline enforcement.
        """
        self.storage = TodoStorage()
        self.settings = TodoSettings()
        self.wallet = WalletManager()
        self.enforce_deadlines()

    def enforce_deadlines(self):
        """
        Hardcore mode: Marks past-due tasks as failed automatically.
        Called on startup.
        """
        now = datetime.datetime.now().astimezone()
        running_tasks = self.storage.read_entries(
            "SELECT task_id, task_name, deadline FROM todo WHERE status = 'Running'"
        )
        for task in running_tasks:
            tid, name, ddl_str = task
            try:
                deadline = datetime.datetime.fromisoformat(ddl_str)
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
        self.storage.write_entries(
            "INSERT INTO todo (task_name, creation_date, deadline, status) VALUES (?, ?, ?, ?)",
            (name, now, deadline_str, "Running")
        )
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
            # Reward: +5 * multiplier
            reward = round(5 * multiplier, 1)
            self.wallet.earn_coins(reward)
            streak += 1
            multiplier = min(2.0, multiplier + 0.1)
            retribution = reward
        else:
            # Penalty (Failed): -2
            self.wallet.earn_coins(-2)
            streak = 0
            multiplier = 1.0
            retribution = -2
            
        self.storage.write_entries(
            "UPDATE todo SET status = ?, completion_time = ?, retribution = ? WHERE task_id = ?",
            (status, now, retribution, task_id)
        )
        self.settings.update_streak_data(streak, round(multiplier, 1))

    def list_running_tasks(self):
        """
        Retrieves current active tasks.

        Takes: None
        Gives: list of records
        """
        return self.storage.read_entries(
            "SELECT task_id, task_name, deadline FROM todo WHERE status = 'Running' ORDER BY deadline ASC"
        )

    def list_finalized_tasks(self, month, year):
        """
        Retrieves tasks finalized (Completed or Failed) in a specific period for the heatmap.

        Takes: month (str), year (str)
        Gives: list of records
        """
        pattern = f"{year}-{month}-%"
        return self.storage.read_entries(
            "SELECT * FROM todo WHERE completion_time LIKE ? AND status IN ('Completed', 'Failed')", 
            (pattern,)
        )


class TodoStatistics:
    """
    Processes data for the overview dashboard using hardcore analytics.
    """

    def __init__(self):
        """
        Initializes the statistics service.
        """
        self.storage = TodoStorage()
        self.settings = TodoSettings()

    def give_overview(self):
        """
        Calculates complex metrics for the overview dashboard.

        Takes: None
        Gives: dict or None
        """
        all_tasks = self.storage.read_entries(
            "SELECT creation_date, deadline, status, completion_time FROM todo"
        )
        config = self.settings.read_config()
        
        if not all_tasks:
            return {
                "streak": config["streak"],
                "multiplier": config["multiplier"],
                "completion_score": 0,
                "focus_score": 0,
                "consistency_trend": [0] * 30,
                "consistency_std": 0,
                "scatter_points": [],
                "total_tasks": 0
            }

        total = len(all_tasks)
        completed = [t for t in all_tasks if t[2] == "Completed"]
        
        comp_count = len(completed)
        comp_score = (comp_count / total * 100) if total > 0 else 0
        
        # Focus Score & Lead Time vs Urgency Scatter Plot
        scatter_points = []
        focus_points = []
        for t in completed:
            try:
                start = datetime.datetime.fromisoformat(t[0])
                ddl = datetime.datetime.fromisoformat(t[1])
                end = datetime.datetime.fromisoformat(t[3])
                
                # Vastness/Broadness: Deadline - Creation
                broadness = (ddl - start).total_seconds() / 3600 # hours
                # Speed to Finish: Completion - Creation
                speed = (end - start).total_seconds() / 3600
                
                scatter_points.append((broadness, speed))
                
                if broadness > 0:
                    ratio = speed / broadness
                    # Score 100 for immediate finish, 0 for last minute
                    score = max(0, 100 * (1 - ratio))
                    focus_points.append(score)
            except (ValueError, TypeError):
                continue

        avg_focus = statistics.mean(focus_points) if focus_points else 0
        
        # Consistency Trend (Standard Deviation over last 30 days)
        now = datetime.datetime.now()
        daily_counts = []
        for i in range(30):
            day = (now - datetime.timedelta(days=i)).strftime("%Y-%m-%d")
            count = sum(1 for t in completed if t[3].startswith(day))
            daily_counts.append(count)
        
        consistency_std = statistics.stdev(daily_counts) if len(daily_counts) > 1 else 0
        
        return {
            "streak": config["streak"],
            "multiplier": config["multiplier"],
            "completion_score": round(comp_score, 1),
            "focus_score": round(avg_focus, 1),
            "consistency_trend": daily_counts[::-1], 
            "consistency_std": round(consistency_std, 2),
            "scatter_points": scatter_points,
            "total_tasks": total
        }
