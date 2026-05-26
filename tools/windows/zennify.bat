:: File Name: zennify.bat
:: Purpose: Universal entry point to run Zennify modules on Windows.

@echo off
setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..\..") do set "PROJECT_ROOT=%%~dpfI"
if "%PROJECT_ROOT:~-1%"=="\" set "PROJECT_ROOT=%PROJECT_ROOT:~0,-1%"

set "CONFIG_FILE=%PROJECT_ROOT%\data\config.json"

if not exist "%CONFIG_FILE%" (
    echo Error: config.json not found at %CONFIG_FILE%. Please run tools\windows\setup.bat first.
    exit /b 1
)

for /f "delims=" %%I in ('python -c "import json; print(json.load(open(r'%CONFIG_FILE%'))['system_config']['venv_path'])"') do set "VENV_PATH=%%I"

if not exist "%VENV_PATH%" (
    echo Error: Virtual environment at %VENV_PATH% not found. Please run tools\windows\setup.bat first.
    exit /b 1
)

set "ZENNIFY_CONFIG_PATH=%CONFIG_FILE%"
set "PYTHONPATH=%PROJECT_ROOT%"

call "%VENV_PATH%\Scripts\activate.bat"
python "%PROJECT_ROOT%\core\main.py" %*

endlocal
