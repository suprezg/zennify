"""
File Name: configurator.py
Purpose: Centralized configuration management for the Zennify application.
"""

import json
import os


class ConfigManager:
    """
    Manages reading and updating configuration values from config.json.
    """

    def __init__(self):
        """
        Initializes the ConfigManager and locates the configuration file.

        Takes: None
        Gives: None
        """
        self.config_path = os.getenv("ZENNIFY_CONFIG_PATH")
        if not self.config_path:
            self.config_path = os.path.join(os.getcwd(), "config.json")

    def read_value(self, feature, key):
        """
        Reads a specific configuration value for a given feature.

        Takes: feature (str), key (str)
        Gives: any (value) or None
        """
        if os.path.exists(self.config_path):
            with open(self.config_path, "r") as f:
                config = json.load(f)
                feature_key = f"{feature}_config"
                return config.get(feature_key, {}).get(key)
        return None

    def update_value(self, feature, key, value):
        """
        Updates a specific configuration value for a given feature.

        Takes: feature (str), key (str), value (any)
        Gives: None
        """
        if os.path.exists(self.config_path):
            with open(self.config_path, "r") as f:
                config = json.load(f)

            feature_key = f"{feature}_config"
            if feature_key not in config:
                config[feature_key] = {}

            config[feature_key][key] = value

            with open(self.config_path, "w") as f:
                json.dump(config, f, indent=4)
