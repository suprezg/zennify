# Architecture and System Design

## 1. High-Level Overview

Zennify is a local-first, privacy-focused productivity ecosystem. It is built as a modular Python application that leverages the Flet framework for cross-platform GUI rendering. The system is designed to run entirely offline, persisting data in a local SQLite database and configuration settings in a JSON file.

### Design Philosophy
*   **Privacy-First**: No external APIs, cloud syncing, or background telemetry.
*   **Low Overhead**: Minimal CPU/RAM footprint during background monitoring.
*   **Gamified Economy**: A unified reward system where productivity earns "coins" used to unlock user-defined rewards.

## 2. Component Architecture

Zennify follows a structured layering pattern to separate UI logic from business rules and data management.

### Presentation Layer
*   **Dashboards (`core/*/dashboard.py`)**: Flet-based UI modules that handle user interaction and data visualization.
*   **Popups (`core/activity/popup.py`)**: Transient interfaces triggered by OS-level timers for periodic activity logging.

### Service Layer (`core/*/service.py`)
*   **Business Logic**: Contains the rules for reward calculations, SRS scheduling (FSRS v6), and timer state machines.
*   **Process Orchestration**: Bridges the gap between the interactive UI and the static storage.

### Data Layer (`core/shared/`)
*   **StorageManager (`storage.py`)**: A centralized SQLite interface using parameterized queries to prevent injection.
*   **ConfigManager (`configurator.py`)**: Manages `config.json`, which stores non-relational settings like project paths and systemd paths.
*   **WalletManager (`wallet.py`)**: The engine of the virtual economy, handling balance updates and debt enforcement.

## 3. Database Schema

The system uses a single SQLite database (`zennify_storage.db`) with the following core tables:

| Table | Purpose | Key Fields |
| :--- | :--- | :--- |
| `activity` | Logs interval work | `session_id`, `date`, `start_time`, `end_time`, `description`, `tag`, `is_productive`, `retribution` |
| `flashcard` | SRS revision data | `card_id`, `content_hash`, `deck_name`, `stability`, `difficulty`, `state`, `next_review`, `last_review` |
| `todo` | Hardcore task list | `task_id`, `task_name`, `creation_date`, `deadline`, `status`, `completion_time`, `retribution` |
| `pomodoro` | Focus session logs | `session_id`, `date`, `start_time`, `end_time`, `duration_mins`, `phase` |
| `shop` | Custom reward items | `item_id`, `item_name`, `cost`, `purchase_count` |
| `wallet` | Virtual economy state | `id=1`, `total_coins`, `bankruptcy_count` |

## 4. OS Integrations

To maintain consistency without a heavy background daemon, Zennify utilizes native OS scheduling tools:

*   **Linux**: Systemd user services (`.service`) and timers (`.timer`) are generated in `$HOME/.config/systemd/user/`.
*   **Windows**: The `schtasks` utility creates a scheduled task (`ZennifyActivityTask`) triggered every 30 minutes.

These scheduled tasks invoke the `zennify --activity-popup` command, ensuring users stay accountable even when the main dashboard is closed.
