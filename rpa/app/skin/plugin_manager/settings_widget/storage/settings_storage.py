"""
SettingsStorage - JSON-based settings persistence.

Handles loading and saving settings to JSON files with
support for custom file paths and default locations.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional


class SettingsStorage:
    """
    JSON-based storage backend for settings.

    Features:
    - Default file location in user config directory
    - Custom file path support
    - Atomic writes to prevent corruption
    - Backup on save

    Follows the Strategy pattern, allowing different storage
    implementations to be swapped.
    """

    def __init__(
        self,
        default_path: Optional[str] = None,
        app_name: str = "settings_widget"
    ):
        """
        Initializes the storage backend.

        Args:
            default_path: Default file path (auto-generated if None)
            app_name: Application name for default path generation
        """
        self._app_name = app_name
        self._default_path = default_path or self._get_default_path()

    def _get_default_path(self) -> str:
        """
        Generates the default settings file path.

        Uses platform-appropriate config directories.

        Returns:
            Path to default settings file
        """
        # Get user config directory
        if os.name == "nt":  # Windows
            config_dir = os.environ.get("APPDATA", os.path.expanduser("~"))
        else:  # Linux/Mac
            config_dir = os.environ.get(
                "XDG_CONFIG_HOME",
                os.path.expanduser("~/.config")
            )

        # Create app config directory
        app_config_dir = os.path.join(config_dir, self._app_name)
        os.makedirs(app_config_dir, exist_ok=True)

        return os.path.join(app_config_dir, "settings.json")

    @property
    def default_path(self) -> str:
        """Returns the default settings file path."""
        return self._default_path

    def load(self, path: Optional[str] = None) -> Dict[str, Any]:
        """
        Loads settings from a JSON file.

        Args:
            path: File path (uses default if None)

        Returns:
            Dictionary of setting values

        Raises:
            FileNotFoundError: If file doesn't exist
            json.JSONDecodeError: If file is invalid JSON
        """
        file_path = path or self._default_path

        if not os.path.exists(file_path):
            return {}

        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def save(
        self,
        values: Dict[str, Any],
        path: Optional[str] = None,
        create_backup: bool = True
    ) -> None:
        """
        Saves settings to a JSON file.

        Uses atomic write to prevent corruption.

        Args:
            values: Dictionary of setting values
            path: File path (uses default if None)
            create_backup: Whether to backup existing file
        """
        file_path = path or self._default_path

        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # Create backup if file exists
        if create_backup and os.path.exists(file_path):
            backup_path = f"{file_path}.bak"
            try:
                if os.path.exists(backup_path):
                    os.remove(backup_path)
                os.rename(file_path, backup_path)
            except OSError:
                pass  # Backup failed, continue anyway

        # Write to temp file first (atomic write)
        temp_path = f"{file_path}.tmp"
        try:
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(values, f, indent=2, ensure_ascii=False)

            # Replace original with temp
            if os.path.exists(file_path):
                os.remove(file_path)
            os.rename(temp_path, file_path)

        except Exception:
            # Clean up temp file on failure
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise

    def delete(self, path: Optional[str] = None) -> bool:
        """
        Deletes the settings file.

        Args:
            path: File path (uses default if None)

        Returns:
            True if file was deleted
        """
        file_path = path or self._default_path

        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False

    def exists(self, path: Optional[str] = None) -> bool:
        """
        Checks if settings file exists.

        Args:
            path: File path (uses default if None)

        Returns:
            True if file exists
        """
        file_path = path or self._default_path
        return os.path.exists(file_path)

    def get_backup_path(self, path: Optional[str] = None) -> str:
        """
        Gets the backup file path.

        Args:
            path: Original file path

        Returns:
            Path to backup file
        """
        file_path = path or self._default_path
        return f"{file_path}.bak"

    def restore_backup(self, path: Optional[str] = None) -> bool:
        """
        Restores settings from backup.

        Args:
            path: File path (uses default if None)

        Returns:
            True if backup was restored
        """
        file_path = path or self._default_path
        backup_path = self.get_backup_path(file_path)

        if os.path.exists(backup_path):
            if os.path.exists(file_path):
                os.remove(file_path)
            os.rename(backup_path, file_path)
            return True
        return False
