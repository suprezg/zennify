### Goal
The goal of `service.py` is to provide the core logic and data management for the Activity Tracker feature. It handles database interactions, configuration management, and the generation of system-level background services.

### Structure
The file contains several classes:
- `ActivityStorage`: Manages CRUD operations for activity records in the database.
- `ActivitySettings`: Manages module-specific settings and systemd integration using `ConfigManager`.
- `ActivityStatistics`: Aggregates activity data for visualization.
- `ActivityReview`: Prepares data for the heatmap and detailed daily logs.

### Logic
- `ActivityStorage` uses `StorageManager` to execute SQL queries for reading and writing activity entries.
- `ActivitySettings` delegates configuration tasks to `ConfigManager` and handles the regeneration of systemd unit files when timers are updated.
- `ActivityStatistics` processes raw database entries into productivity ratios and tag frequencies.
- `ActivityReview` maps database records to day-wise frequencies for the heatmap.

### Extension
New statistics can be added by extending `ActivityStatistics`. The storage logic can be updated to support more complex activity types or additional metadata.
