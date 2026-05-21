#!/bin/bash
# File Name: setup.sh
# Purpose: Initialize the Zennify development environment on Linux.

set -e

SCRIPT_DIR=$(dirname "$(readlink -f "$0")")
PROJECT_ROOT=$(readlink -f "$SCRIPT_DIR/../..")
DATA_DIR="$PROJECT_ROOT/data"

echo "Setting up Zennify at $PROJECT_ROOT..."
mkdir -p "$DATA_DIR"

read -p "Enter your name: " USER_NAME

echo "Creating virtual environment in $DATA_DIR..."
if [ ! -d "$DATA_DIR/.venv" ]; then
    python3 -m venv "$DATA_DIR/.venv"
fi
source "$DATA_DIR/.venv/bin/activate"
VENV_PATH="$DATA_DIR/.venv"
echo "Virtual Environment Created at $VENV_PATH"

echo "Installing dependencies..."
REQUIREMENTS_FILE="$PROJECT_ROOT/tools/requirements.txt"
if [ -f "$REQUIREMENTS_FILE" ]; then
    pip install --upgrade pip
    pip install -r "$REQUIREMENTS_FILE"
else
    echo "Warning: $REQUIREMENTS_FILE not found."
fi

echo "Initializing database..."
PYTHONPATH="$PROJECT_ROOT" python3 -c "
from core.shared.storage import StorageManager
import os
storage = StorageManager(db_path='$DATA_DIR/zennify_storage.db')
storage.close()
"
DB_PATH="$DATA_DIR/zennify_storage.db"
echo "Database Initialized at $DB_PATH"

echo "Generating structured config.json in $DATA_DIR..."
python3 -c "
import json, os
config = {
    \"system_config\": {
        \"user_name\": \"$USER_NAME\",
        \"venv_path\": \"$VENV_PATH\",
        \"database_path\": \"$DB_PATH\",
        \"project_root\": \"$PROJECT_ROOT\"
    },
    \"activity_config\": {
        \"service_path\": os.path.expanduser(\"~/.config/systemd/user/zennify-activity.service\"),
        \"service_status\": False,
        \"popup_interval_timer\": \"30m\",
        \"popup_visible_timer\": \"2m\",
        \"streak\": 0,
        \"multiplier\": 1.0
    },
    \"flashcard_config\": {
        \"flashcard_folder\": \"flashcards\",
        \"streak\": 0,
        \"multiplier\": 1.0
    },
    \"todo_config\": {
        \"service_path\": os.path.expanduser(\"~/.config/systemd/user/zennify-todo.service\"),
        \"service_status\": False,
        \"todo_interval_timer\": \"1h\",
        \"streak\": 0,
        \"multiplier\": 1.0
    },
    \"pomodoro_config\": {},
    \"shop_config\": {}
}
with open('$DATA_DIR/config.json', 'w') as f:
    json.dump(config, f, indent=4)
"
echo "Config File Generated at $DATA_DIR/config.json"


echo "Generating systemd user services..."
mkdir -p ~/.config/systemd/user/

ZENNIFY_SH="$PROJECT_ROOT/tools/linux/zennify.sh"

cat <<EOF > ~/.config/systemd/user/zennify-activity.service
[Unit]
Description=Zennify Activity Tracking Service
After=network.target

[Service]
ExecStart=$ZENNIFY_SH --activity-popup
Restart=always

[Install]
WantedBy=default.target
EOF

cat <<EOF > ~/.config/systemd/user/zennify-todo.service
[Unit]
Description=Zennify Todo Service
After=network.target

[Service]
ExecStart=$ZENNIFY_SH --todos
Restart=always

[Install]
WantedBy=default.target
EOF

systemctl --user daemon-reload
echo "Systemd services generated at ~/.config/systemd/user/"

echo "Setup complete. Use $ZENNIFY_SH to run the application."
