# Testing Strategies and Verification Results

## 1. Testing Philosophy

Zennify prioritizes the validation of business logic (Service Layer) and data integrity (Data Layer) over visual regression. The testing strategy is divided into two primary tiers:

1.  **Automated Unit Testing**: Fast, isolated tests for core logic.
2.  **Manual Integration Verification**: Platform-specific checks for OS-level integrations.

## 2. Automated Testing Suite

The project uses `pytest` for all automated validations.

### Test Environment Isolation
*   **Database Isolation**: Tests utilize temporary SQLite database files created via `tmp_path` fixtures, ensuring local user data is never modified.
*   **Configuration Isolation**: The `ZENNIFY_CONFIG_PATH` environment variable is mocked or redirected to temporary files during test execution.
*   **UI Mocking**: Since dashboards are built with Flet, we use `unittest.mock.MagicMock` to simulate the `flet.Page` object. This allows us to verify that the correct UI components are instantiated without requiring a display server or window manager.

### Test Structure
All tests are located in the `tests/` directory following a flat file structure:
*   `test_shared_*.py`: Validates foundational storage and configurator logic.
*   `test_<feature>_service.py`: Validates mathematical calculations, FSRS logic, and DB operations.
*   `test_<feature>_dashboard.py`: Validates routing and component assembly.

### Running Tests
To execute the full suite, run the following command from the project root:
```bash
python3 -m pytest tests/
```

## 3. Manual Verification Procedures

Certain system integrations must be verified manually on the target operating system.

### Platform-Specific Integration Checks

#### Linux (Systemd)
1.  **Timer Generation**: Run `bash tools/linux/setup.sh` and verify that `~/.config/systemd/user/zennify-activity.timer` exists.
2.  **Service Status**: Run `systemctl --user list-timers` and ensure `zennify-activity.timer` is listed and active.

#### Windows (Task Scheduler)
1.  **Task Creation**: Run `tools\windows\setup.bat` in an administrative Command Prompt.
2.  **Task Verification**: Run `schtasks /query /tn "ZennifyActivityTask"` to confirm the task is correctly registered.

### Functional Smoke Tests
1.  **CLI Routing**: Verify that `./zennify.sh --help` (Linux) or `zennify.bat --help` (Windows) displays the correct usage guide.
2.  **Bankruptcy Reset**: Verify that running with the `--bankrupt` flag correctly resets the coin balance in the SQLite `wallet` table.
