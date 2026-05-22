### Goal
The goal of `popup.py` is to provide an interactive window that periodically prompts the user to log their recent activity. It calculates rewards based on productivity streaks and multipliers.

### Structure
The file contains the `ActivityPopup` class, which uses Flet to display a small, always-on-top window. It interacts with `ActivitySettings`, `ActivityStorage`, and `ConfigManager`.

### Logic
- `__init__`: Initializes timers based on the centralized configuration.
- `view()`: Sets up the popup UI, including tag selection and productivity radio buttons.
- `_countdown_timer()`: An asynchronous task that updates the remaining time and auto-submits as "Inactive" if the user doesn't respond.
- `_submit()`: Calculates the reward (coins) based on whether the activity was productive and updates the user's streak and multiplier in the configuration.
- `_parse_timer()`: Converts human-readable timer strings (e.g., '30m') into seconds.

### Extension
The popup could be enhanced with more detailed productivity categories or integration with other features like Pomodoro or Todo lists.
