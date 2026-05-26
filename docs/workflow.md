# Process Flow and Operation Sequences

## 1. Application Initialization

The Zennify lifecycle begins with environment setup and proceeds to dynamic CLI routing.

1.  **Environment Setup**: 
    *   `tools/linux/setup.sh` or `tools/windows/setup.bat` is executed.
    *   A Python virtual environment is created in `data/.venv`.
    *   Dependencies are installed via `uv pip`.
    *   `zennify_storage.db` is initialized with the schema.
    *   OS-level background timers (Systemd/Task Scheduler) are generated.
2.  **CLI Wrapper**:
    *   `zennify.sh/.bat` locates the `config.json`, activates the virtual environment, sets the `PYTHONPATH`, and passes all arguments to `core/main.py`.
3.  **Routing**:
    *   `core/main.py` parses flags (e.g., `--activity`, `--pomodoro`) and instantiates the corresponding Dashboard class, calling its `.view()` method.

## 2. Core Gamification Loop

The virtual economy is the "glue" that binds all modules.

1.  **Trigger**: User completes a task (Todo), logs an interval (Activity).
2.  **Calculation**:
    *   Retrieves the current `streak` and `multiplier` from `config.json`.
    *   *Productive Result*: `Reward = Base * Multiplier`. Increment streak and increase multiplier (capped at 2.0x).
    *   *Unproductive Result*: `Penalty = Fixed Negative Value`. Reset streak to 0 and multiplier to 1.0x.
3.  **Wallet Update**: `WalletManager` updates the `total_coins` in SQLite. Balance can go negative down to a "debt limit" of -75 coins.
4.  **Bankruptcy Protocol**: 
    *   If the user balance is negative, a warning is displayed.
    *   The user can manually trigger `--bankrupt`, which resets coins to 0, resets all streaks/multipliers to default, and increments the `bankruptcy_count`.

## 3. Sub-System Operation Sequences

### Flashcard Revision (FSRS v6)
*   **Scan**: `FlashcardRevision.scan_folder()` walks the user's Markdown directory.
*   **Hash**: It uses MD5 hashes of questions to track card identity and hashes of (Question+Answer) to detect content updates.
*   **Schedule**: When a card is rated (Again/Hard/Good/Easy), the FSRS algorithm calculates the new `stability` and `difficulty`, setting the `next_review` timestamp.

### Hardcore Todo Management
*   **Deadline Enforcement**: On every startup, `TodoTasks.enforce_deadlines()` compares the current time with the `deadline` of all "Running" tasks.
*   **Automatic Failure**: Any task past its deadline is automatically marked as "Failed," resulting in a coin penalty and streak reset.

### Pomodoro Timer
*   **State Machine**: Transitions through `Work` -> `Short Break` -> `Work` -> `Long Break`.
*   **Persistence**: The current timer state (remaining seconds, phase, running status) is saved to `data/pomodoro_state.json` on every state change, allowing the timer to survive application restarts.
