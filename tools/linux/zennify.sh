#!/bin/bash
# File Name: zennify.sh
# Purpose: Universal entry point to run Zennify modules on Linux.

if [ ! -f "config.json" ]; then
    echo "Error: config.json not found. Please run tools/linux/setup.sh first."
    exit 1
fi

VENV_PATH=$(python3 -c "import json; print(json.load(open('config.json'))['system_config']['venv_path'])")

if [ ! -d "$VENV_PATH" ]; then
    echo "Error: Virtual environment at $VENV_PATH not found. Please run tools/linux/setup.sh first."
    exit 1
fi

source "$VENV_PATH/bin/activate"
PYTHONPATH=. python3 core/main.py "$@"
