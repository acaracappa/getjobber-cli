"""Configuration management for GetJobber CLI."""

import json
import os
from pathlib import Path
from typing import Any, Optional

from getjobber_cli.constants import (
    CONFIG_DIR_NAME,
    CONFIG_FILE_NAME,
    DEFAULT_ITEMS_PER_PAGE,
    DEFAULT_OUTPUT_FORMAT,
)


class Config:
    """Manages configuration file for GetJobber CLI."""

    def __init__(self, config_dir: Optional[Path] = None):
        """Initialize configuration manager.

        Args:
            config_dir: Optional custom config directory path.
                       Defaults to ~/.getjobber
        """
        if config_dir is None:
            self.config_dir = Path.home() / CONFIG_DIR_NAME
        else:
            self.config_dir = config_dir

        self.config_file = self.config_dir / CONFIG_FILE_NAME
        self._config: dict[str, Any] = {}
        self._ensure_config_dir()
        self._load()

    def _ensure_config_dir(self) -> None:
        """Create config directory if it doesn't exist."""
        if not self.config_dir.exists():
            self.config_dir.mkdir(parents=True, exist_ok=True)
            # Set directory permissions to 0700 (user read/write/execute only)
            self.config_dir.chmod(0o700)

    def _load(self) -> None:
        """Load configuration from file."""
        if self.config_file.exists():
            try:
                with open(self.config_file, "r") as f:
                    self._config = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                # If config file is corrupted, start with empty config
                self._config = {}
        else:
            # Initialize with default config
            self._config = self._get_default_config()
            self._save()

    def _save(self) -> None:
        """Save configuration to file."""
        try:
            with open(self.config_file, "w") as f:
                json.dump(self._config, f, indent=2)
            # Set file permissions to 0600 (user read/write only)
            self.config_file.chmod(0o600)
        except IOError as e:
            raise IOError(f"Failed to save configuration: {e}")

    def _get_default_config(self) -> dict[str, Any]:
        """Get default configuration values.

        Returns:
            Dictionary with default configuration.
        """
        return {
            "client_id": "",
            "client_secret": "",
            "default_output_format": DEFAULT_OUTPUT_FORMAT,
            "items_per_page": DEFAULT_ITEMS_PER_PAGE,
        }

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value.

        Args:
            key: Configuration key.
            default: Default value if key not found.

        Returns:
            Configuration value or default.
        """
        return self._config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set configuration value.

        Args:
            key: Configuration key.
            value: Configuration value.
        """
        self._config[key] = value
        self._save()

    def delete(self, key: str) -> bool:
        """Delete configuration key.

        Args:
            key: Configuration key to delete.

        Returns:
            True if key was deleted, False if key didn't exist.
        """
        if key in self._config:
            del self._config[key]
            self._save()
            return True
        return False

    def get_all(self) -> dict[str, Any]:
        """Get all configuration values.

        Returns:
            Dictionary with all configuration.
        """
        return self._config.copy()

    def reset(self) -> None:
        """Reset configuration to defaults."""
        self._config = self._get_default_config()
        self._save()

    def is_configured(self) -> bool:
        """Check if OAuth credentials are configured.

        Returns:
            True if client_id and client_secret are set.
        """
        client_id = self.get("client_id", "")
        client_secret = self.get("client_secret", "")
        return bool(client_id) and bool(client_secret)


def get_config() -> Config:
    """Get global configuration instance.

    Returns:
        Config instance.
    """
    return Config()
