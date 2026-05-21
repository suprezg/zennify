#!/bin/bash
# File Name: zennify.sh
# Purpose: Universal entry point to run Zennify modules on Linux.

SCRIPT_DIR=$(dirname "$(readlink -f "$0")")
PROJECT_ROOT=$(readlink -f "$SCRIPT_DIR/../..")
CONFIG_FILE="$PROJECT_ROOT/data/config.json"

if [ ! -f "$CONFIG_FILE" ]; then
    echo "Error: config.json not found at $CONFIG_FILE. Please run tools/linux/setup.sh first."
    exit 1
fi

VENV_PATH=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE'))['system_config']['venv_path'])")

if [ ! -d "$VENV_PATH" ]; then
    echo "Error: Virtual environment at $VENV_PATH not found. Please run tools/linux/setup.sh first."
    exit 1
fi

export ZENNIFY_CONFIG_PATH="$CONFIG_FILE"

source "$VENV_PATH/bin/activate"
PYTHONPATH="$PROJECT_ROOT" python3 "$PROJECT_ROOT/core/main.py" "$@"
