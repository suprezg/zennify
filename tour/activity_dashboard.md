### Goal
The goal of `dashboard.py` is to provide the main user interface for the Activity Tracker feature. it allows users to review their activity history via a heatmap, view productivity statistics through various charts, and manage background service settings.

### Structure
The file contains the `ActivityDashboard` class, which uses the Flet framework for the UI. It organizes the interface into three tabs: Review, Overview, and Settings. It interacts with `ActivitySettings`, `ActivityStatistics`, `ActivityReview`, and the new `ConfigManager`.

### Logic
- `view()`: Configures the page and sets up the tab navigation.
- `_review_tab()`: Implements a month/year picker and a heatmap showing activity frequency for each day.
- `_overview_tab()`: Displays productivity metrics (streak, multiplier) and visualizes data using pie, radar, and bar charts.
- `_settings_tab()`: Provides controls for toggling the background service and adjusting popup timers.
- Navigation and interaction are handled via Flet event handlers that call methods in the service classes.

### Extension
The dashboard can be extended by adding more visualizations to the Overview tab or by implementing more detailed activity filtering options in the Review tab.
