# Installation and Usage Guidelines

Welcome to Zennify. This guide provides detailed instructions to set up the gamified productivity ecosystem on your local machine and how to utilize its various features effectively.

### Linux (Recommended)

1.  **Clone the Repository**:
    ```bash
    git clone https://github.com/your-repo/zennify.git
    cd zennify
    ```

2.  **Run Setup Script**:
    Execute the automated setup script to create a virtual environment and install dependencies:
    ```bash
    bash tools/linux/setup.sh
    ```

### Windows

1.  **Clone the Repository**:
    ```cmd
    git clone https://github.com/your-repo/zennify.git
    cd zennify
    ```

2.  **Run Setup Batch**:
    ```cmd
    tools\windows\setup.bat
    ```

## 2. Usage Guidelines

Zennify is operated primarily through the command line using the `zennify` wrapper script (or direct execution of `core/main.py` within the virtual environment).

### Command Syntax

```bash
# Linux
bash tools/linux/zennify.sh [flag]

# Windows
tools\windows\zennify.bat [flag]
```

### Available Flags

-   **`--activity`**: Launches the Activity Tracker dashboard for logging interval-based work and viewing productivity trends.
-   **`--flashcards`**: Opens the Spaced-Repetition System (SRS) dashboard for card revision and knowledge management.
-   **`--todos`**: Accesses the Hardcore Todo manager for deadline-enforced task tracking.
-   **`--pomodoro`**: Starts the Pomodoro timer with integrated focus analytics.
-   **`--shop`**: Opens the virtual Shop where you can spend earned coins on custom rewards.
-   **`--bankrupt`**: (Maintenance) Manually triggers the bankruptcy protocol if your coin balance is severely negative.
-   **`--help`**: Displays the Help Message.

## 3. Troubleshooting

-   **Module Not Found**: Ensure you are running the scripts through the provided `zennify.sh`/`zennify.bat` wrappers which automatically activate the virtual environment.
-   **Database Errors**: If the database becomes corrupted, you can reset it by deleting the `data/` directory and re-running the setup script (Note: This will erase all progress).
-   **GUI Scaling**: If the Flet window appears too small or large, adjust your system's display scaling settings; Zennify uses responsive layouts to compensate.
