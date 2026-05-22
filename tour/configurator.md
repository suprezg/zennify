### Goal
The goal of the `configurator.py` file is to provide a centralized and consistent way to manage configuration settings across various features of the Zennify application. It simplifies the process of reading from and writing to the `config.json` file.

### Structure
The file contains a single class, `ConfigManager`, which encapsulates the logic for interacting with the configuration file. It uses the `json` module for parsing and the `os` module for file path and environment variable management.

### Logic
The `ConfigManager` determines the path to the configuration file using the `ZENNIFY_CONFIG_PATH` environment variable, defaulting to `config.json` in the current working directory.
- `read_value(feature, key)`: This method constructs a feature-specific key (e.g., `activity_config`), reads the JSON file, and retrieves the value associated with the provided key within that feature's configuration.
- `update_value(feature, key, value)`: This method reads the current configuration, updates or creates the value for the specified feature and key, and then writes the updated configuration back to the file with indentation for readability.

### Extension
The `ConfigManager` can be extended to support more features by simply adding new feature names to the allowed set of parameters. It could also be enhanced to support default values or configuration validation in the future.
