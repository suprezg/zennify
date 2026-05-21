#!/bin/bash
# File Name: setup.sh
# Purpose: Initialize the Zennify development environment on Linux.

set -e

echo "Setting up Zennify..."

read -p "Enter your name: " USER_NAME

echo "Creating virtual environment..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi
source .venv/bin/activate
VENV_PATH=$(pwd)/.venv
echo "Virtual Environment Created at $(pwd)"

echo "Installing dependencies..."
if [ -f "tools/requirements.txt" ]; then
    pip install --upgrade pip
    pip install -r tools/requirements.txt
else
    echo "Warning: tools/requirements.txt not found."
fi

echo "Initializing database..."
python3 -c "
from core.shared.storage import StorageManager
storage = StorageManager()
storage.close()
"
DB_PATH=$(pwd)/zennify_storage.db
echo "Database Initialized at $(pwd)"

echo "Generating structured config.json..."
python3 -c "
import json, os
config = {
    \"system_config\": {
        \"user_name\": \"$USER_NAME\",
        \"venv_path\": \"$VENV_PATH\",
        \"database_path\": \"$DB_PATH\"
    },
    \"activity_config\": {
        \"service_path\": os.path.expanduser(\"~/.config/systemd/user/zennify-activity.service\"),
        \"service_status\": False,
        \"popup_interval_timer\": \"30m\",
        \"popup_visible_timer\": \"1m\",
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
with open('config.json', 'w') as f:
    json.dump(config, f, indent=4)
"
echo "Config File Generated at $(pwd)"


echo "Generating systemd user services..."
mkdir -p ~/.config/systemd/user/

cat <<EOF > ~/.config/systemd/user/zennify-activity.service
[Unit]
Description=Zennify Activity Tracking Service
After=network.target

[Service]
ExecStart=$(pwd)/tools/linux/zennify.sh --activity-popup
Restart=always

[Install]
WantedBy=default.target
EOF

cat <<EOF > ~/.config/systemd/user/zennify-todo.service
[Unit]
Description=Zennify Todo Service
After=network.target

[Service]
ExecStart=$(pwd)/tools/linux/zennify.sh --todos
Restart=always

[Install]
WantedBy=default.target
EOF

systemctl --user daemon-reload
echo "Systemd services generated at ~/.config/systemd/user/"

echo "Setup complete. Use tools/linux/zennify.sh to run the application."
