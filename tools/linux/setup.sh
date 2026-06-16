#!/bin/bash
# File Name: setup.sh
# Purpose: Initialize the Zennify development environment on Linux.

set -euo pipefail

setup_data_folder() {
    echo "Creating Data folder in $PROJECT_ROOT"
    DATA_ROOT="$PROJECT_ROOT/data"
    mkdir -p "$DATA_ROOT"
    echo "Created Data Folder"
}

setup_virtual_environment() {
    echo "Creating Virtual Environment in $DATA_ROOT..."
    if [ ! -d "$DATA_ROOT/.venv" ]; then
        python3 -m venv "$DATA_ROOT/.venv"
    fi
    VENV_PATH="$DATA_ROOT/.venv"
    echo "Virtual Environment Created"
}

install_dependencies() {
    echo "Installing Dependencies..."
    source "$VENV_PATH/bin/activate"
    if [ -f "$PROJECT_ROOT/tools/dependencies.txt" ]; then
        pip install -q --upgrade pip uv
        uv pip install -r "$PROJECT_ROOT/tools/dependencies.txt"
    else
        echo "Warning: $PROJECT_ROOT/tools/dependencies.txt not found."
    fi
    echo "Dependencies Installed"
}

initialize_database() {
    echo "Initializing Database in $DATA_ROOT..."
    PYTHONPATH="$PROJECT_ROOT" python3 -c "
    from core.shared.storage import StorageManager
    import os
    storage = StorageManager(db_path='$DATA_ROOT/zennify_storage.db')
    storage.close()
    "
    DB_PATH="$DATA_ROOT/zennify_storage.db"
    echo "Database Initialized"
}

generate_service() {
    echo "Generating Systmd User Services in $HOME/.config/systemd/user/..."
    mkdir -p $HOME/.config/systemd/user/

    ZENNIFY_SH="$PROJECT_ROOT/tools/linux/zennify.sh"

    cat <<EOF > $HOME/.config/systemd/user/zennify-activity.service
[Unit]
Description=Zennify Activity Tracking Service

[Service]
Type=oneshot
ExecStart=$ZENNIFY_SH --activity-popup
EOF

    cat <<EOF > $HOME/.config/systemd/user/zennify-activity.timer
[Unit]
Description=Zennify Activity Tracking Timer

[Timer]
OnActiveSec=30m
OnUnitActiveSec=30m
Persistent=false

[Install]
WantedBy=timers.target
EOF

    systemctl --user daemon-reload
    echo "Systemd Services Generated"

}

generate_config() {
    echo "Generating Config File in $DATA_ROOT..."
    python3 -c "
    import json, os
    config = {
        \"system_config\": {
            \"project_root\": \"$PROJECT_ROOT\",
            \"venv_path\": \"$VENV_PATH\",
            \"database_path\": \"$DB_PATH\"
        },
        \"activity_config\": {
            \"service_path\": os.path.expanduser(\"$HOME/.config/systemd/user/zennify-activity.service\"),
            \"timer_path\": os.path.expanduser(\"$HOME/.config/systemd/user/zennify-activity.timer\"),
            \"service_status\": False,
            \"popup_interval_timer\": \"30m\",
            \"popup_visible_timer\": \"2m\",
            \"streak\": 0,
            \"multiplier\": 1.0
        },
        \"flashcard_config\": {
            \"folder_paths\": [\"$PROJECT_ROOT\"]
        },
        \"todo_config\": {
            \"max_tasks\": 5,
            \"streak\": 0,
            \"multiplier\": 1.0
        },
        \"pomodoro_config\": {
            \"work_time\": \"60m\",
            \"short_break_time\": \"5m\",
            \"long_break_time\": \"15m\",
            \"long_break_interval\": \"2\"
        }
    }
    with open('$DATA_ROOT/config.json', 'w') as f:
        json.dump(config, f, indent=4)
    "
    echo "Config File Generated"
}

main() {
    SCRIPT_DIR=$(dirname "$(readlink -f "$0")")
    PROJECT_ROOT=$(readlink -f "$SCRIPT_DIR/../..")

    echo "Setting up Zennify at $PROJECT_ROOT..."
    setup_data_folder
    setup_virtual_environment
    install_dependencies
    initialize_database
    generate_service
    generate_config
    echo "Setup complete. Use $ZENNIFY_SH to run the application."
}

main
