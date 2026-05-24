"""
File Name: configurator.py
Purpose: Centralized configuration management for the Zennify application.
"""

import json
import os


class ConfigManager:
    """
    Manages reading and updating configuration values from config.json.
    Provides a unified interface for feature-specific settings.
    """

    def __init__(self):
        """
        Initializes the ConfigManager and locates the configuration file path.

        Takes:
            None: Retrieves the configuration path from environment variables.

        Gives:
            None: Sets the internal 'config_path' attribute.
        """
        self.config_path = os.getenv("ZENNIFY_CONFIG_PATH")

    def read_value(self, feature, key):
        """
        Reads a specific configuration value for a given feature.

        Takes:
            feature (str): The name of the feature (e.g., 'activity', 'pomodoro').
            key (str): The specific setting key to retrieve.

        Gives:
            any: The value associated with the key, or None if the feature or key is missing.
        """
        with open(self.config_path, "r") as f:
            config = json.load(f)
            feature_key = f"{feature}_config"
            return config.get(feature_key, {}).get(key)

    def update_value(self, feature, key, value):
        """
        Updates a specific configuration value for a given feature and persists it.

        Takes:
            feature (str): The name of the feature to update.
            key (str): The specific setting key to modify.
            value (any): The new value to assign to the key.

        Gives:
            None: Updates the configuration dictionary and writes it back to the file.
        """
        with open(self.config_path, "r") as f:
            config = json.load(f)

        feature_key = f"{feature}_config"
        if feature_key not in config:
            config[feature_key] = {}

        config[feature_key][key] = value

        with open(self.config_path, "w") as f:
            json.dump(config, f, indent=4)
