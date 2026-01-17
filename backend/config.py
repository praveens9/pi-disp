"""
Configuration Management for Pi Display

This module handles loading configuration from YAML files and environment variables.
It provides a simple interface to access configuration values throughout the application.

Why we need this:
- Keeps sensitive data (API keys) separate from code
- Makes it easy to change settings without editing code
- Allows different configs for development vs production
"""

import os
import yaml
from pathlib import Path


class Config:
    """
    Configuration loader that reads from config.yaml and environment variables.

    Usage:
        config = Config()
        api_key = config.get('weather.api_key')
        latitude = config.get('weather.latitude', default=0.0)
    """

    def __init__(self, config_path=None):
        """
        Initialize the configuration loader.

        Args:
            config_path (str, optional): Path to config.yaml file.
                                        If None, looks in ../config/config.yaml
        """
        # If no path provided, use default location
        if config_path is None:
            # __file__ is the path to this config.py file
            # We go up one level (..) to project root, then into config/
            backend_dir = Path(__file__).parent  # backend/
            project_root = backend_dir.parent     # pi-disp/
            config_path = project_root / 'config' / 'config.yaml'

        self.config_path = Path(config_path)
        self.config_data = {}

        # Load configuration from file
        self._load_config()

    def _load_config(self):
        """
        Load configuration from YAML file.

        This is a private method (starts with _) that's only used internally.
        It reads the YAML file and stores the data in self.config_data.
        """
        # Check if config file exists
        if not self.config_path.exists():
            print(f"⚠️  Warning: Config file not found at {self.config_path}")
            print(f"   Using config/config.yaml.example as template")
            print(f"   Please copy it to config/config.yaml and add your API keys")

            # Try to load from example file instead
            example_path = self.config_path.parent / 'config.yaml.example'
            if example_path.exists():
                self.config_path = example_path
            else:
                # No config at all - use empty dict
                return

        # Read and parse YAML file
        try:
            with open(self.config_path, 'r') as f:
                # yaml.safe_load converts YAML to Python dictionary
                self.config_data = yaml.safe_load(f) or {}
                print(f"✓ Configuration loaded from {self.config_path}")
        except Exception as e:
            print(f"❌ Error loading config: {e}")
            self.config_data = {}

    def get(self, key, default=None):
        """
        Get a configuration value by key.

        Supports nested keys using dot notation:
            'weather.api_key' accesses config['weather']['api_key']

        Args:
            key (str): Configuration key (can be nested with dots)
            default: Value to return if key is not found

        Returns:
            The configuration value, or default if not found

        Examples:
            >>> config.get('weather.api_key')
            'your-api-key-here'

            >>> config.get('weather.latitude', default=0.0)
            40.7128

            >>> config.get('non.existent.key', default='fallback')
            'fallback'
        """
        # First check environment variables (they override config file)
        # Convert 'weather.api_key' to 'WEATHER_API_KEY'
        env_key = key.upper().replace('.', '_')
        env_value = os.getenv(env_key)
        if env_value is not None:
            return env_value

        # Navigate nested dictionary using dot notation
        # 'weather.api_key' becomes ['weather', 'api_key']
        keys = key.split('.')
        value = self.config_data

        # Walk through the nested dictionary
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                # Key not found, return default
                return default

        return value

    def get_section(self, section):
        """
        Get an entire configuration section as a dictionary.

        Args:
            section (str): The section name (e.g., 'weather', 'news')

        Returns:
            dict: The section as a dictionary, or empty dict if not found

        Example:
            >>> config.get_section('weather')
            {'api_key': 'xxx', 'latitude': 40.7128, 'longitude': -74.0060}
        """
        return self.config_data.get(section, {})

    def has(self, key):
        """
        Check if a configuration key exists.

        Args:
            key (str): Configuration key to check

        Returns:
            bool: True if key exists, False otherwise
        """
        return self.get(key) is not None

    def reload(self):
        """
        Reload configuration from file.

        Useful if config file is updated while app is running.
        """
        self._load_config()
        print("✓ Configuration reloaded")


# Create a global config instance that can be imported elsewhere
# This way other files can just do: from config import config
config = Config()


# Example usage (only runs if this file is executed directly)
if __name__ == '__main__':
    print("\n=== Testing Configuration ===\n")

    # Test loading config
    test_config = Config()

    # Test getting values
    print(f"Weather API key: {test_config.get('weather.api_key', 'NOT SET')}")
    print(f"Latitude: {test_config.get('weather.latitude', 0.0)}")
    print(f"Rotation interval: {test_config.get('display.rotation_interval', 30)}")

    # Test section loading
    weather_section = test_config.get_section('weather')
    print(f"\nWeather section: {weather_section}")

    # Test key existence
    has_api_key = test_config.has('weather.api_key')
    print(f"\nHas API key configured: {has_api_key}")
