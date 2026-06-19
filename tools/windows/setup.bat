:: File Name: setup.bat
:: Purpose: Initialize the Zennify development environment on Windows.

@echo off
setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..\..") do set "PROJECT_ROOT=%%~dpfI"
if "%PROJECT_ROOT:~-1%"=="\" set "PROJECT_ROOT=%PROJECT_ROOT:~0,-1%"

echo Setting up Zennify at %PROJECT_ROOT%...

echo Creating Data folder in %PROJECT_ROOT%
set "DATA_ROOT=%PROJECT_ROOT%\data"
if not exist "%DATA_ROOT%" mkdir "%DATA_ROOT%"
echo Created Data Folder

echo Creating Virtual Environment in %DATA_ROOT%...
set "VENV_PATH=%DATA_ROOT%\.venv"
if not exist "%VENV_PATH%" (
    python -m venv "%VENV_PATH%"
)
echo Virtual Environment Created

echo Installing Dependencies...
call "%VENV_PATH%\Scripts\activate.bat"
if exist "%PROJECT_ROOT%\tools\dependencies.txt" (
    python -m pip install -q --upgrade pip uv
    uv pip install -r "%PROJECT_ROOT%\tools\dependencies.txt"
) else (
    echo Warning: %PROJECT_ROOT%\tools\dependencies.txt not found.
)
echo Dependencies Installed

echo Initializing Database in %DATA_ROOT%...
set "DB_PATH=%DATA_ROOT%\zennify_storage.db"
set "PYTHONPATH=%PROJECT_ROOT%"
python -c "from core.shared.storage import StorageManager; import os; db_path=r'%DB_PATH%'.replace('\\', '/'); storage = StorageManager(db_path=db_path); storage.close()"
echo Database Initialized

echo Generating Task Scheduler entry for Zennify Activity...
set "ZENNIFY_BAT=%PROJECT_ROOT%\tools\windows\zennify.bat"
schtasks /create /tn "ZennifyActivityTask" /tr "\"%ZENNIFY_BAT%\" --activity-popup" /sc minute /mo 30 /f >nul 2>&1
echo Task Scheduler entry generated

echo Generating Config File in %DATA_ROOT%...
python -c "import json, os; config = { 'system_config': { 'project_root': r'%PROJECT_ROOT%', 'venv_path': r'%VENV_PATH%', 'database_path': r'%DB_PATH%' }, 'activity_config': { 'service_path': 'ZennifyActivityTask', 'timer_path': 'ZennifyActivityTask', 'service_status': False, 'popup_interval_timer': '30m', 'popup_visible_timer': '2m', 'streak': 0, 'multiplier': 1.0 }, 'flashcard_config': { 'folder_paths': [r'%PROJECT_ROOT%'] }, 'todo_config': { 'max_tasks': 5, 'streak': 0, 'multiplier': 1.0 }, 'pomodoro_config': { 'work_time': '60m', 'short_break_time': '5m', 'long_break_time': '15m', 'long_break_interval': '2' } }; f=open(r'%DATA_ROOT%\config.json', 'w'); json.dump(config, f, indent=4); f.close()"
echo Config File Generated

echo Setup complete. Use %ZENNIFY_BAT% to run the application.
endlocal
