"""
SettingsController - Main controller for settings management.

Coordinates between the settings registry (model) and the UI (view),
handling business logic like validation, persistence, and change propagation.
"""

from typing import Any, Callable, Dict, List, Optional

from rpa.app.plugin_manager.settings_widget.qt_compat import QObject, Signal, Slot
from rpa.app.plugin_manager.settings_widget.models.settings_registry import SettingsRegistry
from rpa.app.plugin_manager.settings_widget.models.setting_item import SettingItem
from rpa.app.plugin_manager.settings_widget.storage.settings_storage import SettingsStorage


class SettingsController(QObject):
    """
    Controller managing settings operations.

    Responsibilities:
    - Coordinating model (registry) and view
    - Managing settings persistence
    - Handling import/export operations
    - Providing undo/redo support (future)

    Follows the Controller pattern in MVC architecture.

    Signals:
        settings_loaded: Emitted after settings are loaded from storage
        settings_saved: Emitted after settings are saved to storage
        SIG_SETTINGS_CHANGED: Emitted when a setting value changes
    """

    settings_loaded = Signal()
    settings_saved = Signal()
    SIG_SETTINGS_CHANGED = Signal(str, object)  # (setting_id, new_value)

    def __init__(
        self,
        registry: Optional[SettingsRegistry] = None,
        storage: Optional[SettingsStorage] = None,
        parent: Optional[QObject] = None
    ):
        """
        Initializes the settings controller.

        Args:
            registry: Settings registry to use
            storage: Storage backend for persistence
            parent: Optional parent QObject
        """
        super().__init__(parent)

        self._registry = registry or SettingsRegistry()
        self._storage = storage or SettingsStorage()

        # Connect to registry changes
        self._registry.SIG_SETTINGS_CHANGED.connect(self._on_setting_changed)

    @property
    def registry(self) -> SettingsRegistry:
        """Returns the settings registry."""
        return self._registry

    @property
    def storage(self) -> SettingsStorage:
        """Returns the storage backend."""
        return self._storage

    def register_setting(self, setting: SettingItem) -> None:
        """
        Registers a new setting.

        Args:
            setting: The setting to register
        """
        self._registry.register_setting(setting)

    def register_settings(
        self,
        settings: List[Dict[str, Any]],
        namespace: str = "",
        category: str = "General"
    ) -> None:
        """
        Batch registers multiple settings.

        Args:
            settings: List of setting configurations
            namespace: Namespace for all settings
            category: Default category
        """
        self._registry.register_settings(settings, namespace, category)

    def get_value(self, setting_id: str, default: Any = None) -> Any:
        """
        Gets a setting value.

        Args:
            setting_id: Full ID of the setting
            default: Default if setting not found

        Returns:
            Current setting value
        """
        return self._registry.get_value(setting_id, default)

    def set_value(self, setting_id: str, value: Any) -> bool:
        """
        Sets a setting value.

        Args:
            setting_id: Full ID of the setting
            value: New value

        Returns:
            True if value was set successfully
        """
        return self._registry.set_value(setting_id, value)

    def reset_setting(self, setting_id: str) -> None:
        """
        Resets a setting to its default.

        Args:
            setting_id: Full ID of the setting
        """
        self._registry.reset_setting(setting_id)

    def reset_all(self) -> None:
        """Resets all settings to defaults."""
        self._registry.reset_all()

    def search(self, query: str) -> List[SettingItem]:
        """
        Searches settings.

        Args:
            query: Search query

        Returns:
            List of matching settings
        """
        return self._registry.search(query)

    def load_settings(self, path: Optional[str] = None) -> bool:
        """
        Loads settings from storage.

        Args:
            path: Optional specific file path

        Returns:
            True if load was successful
        """
        try:
            values = self._storage.load(path)
            self._registry.load_values(values)
            self.settings_loaded.emit()
            return True
        except Exception as e:
            print(f"Error loading settings: {e}")
            return False

    def save_settings(self, path: Optional[str] = None) -> bool:
        """
        Saves settings to storage.

        Args:
            path: Optional specific file path

        Returns:
            True if save was successful
        """
        try:
            values = self._registry.to_dict()
            self._storage.save(values, path)
            self.settings_saved.emit()
            return True
        except Exception as e:
            print(f"Error saving settings: {e}")
            return False

    def export_settings(self, path: str) -> bool:
        """
        Exports settings to a file.

        Args:
            path: File path for export

        Returns:
            True if export was successful
        """
        return self.save_settings(path)

    def import_settings(self, path: str) -> bool:
        """
        Imports settings from a file.

        Args:
            path: File path to import from

        Returns:
            True if import was successful
        """
        return self.load_settings(path)

    def get_modified_settings(self) -> List[SettingItem]:
        """Returns settings that differ from defaults."""
        return self._registry.get_modified_settings()

    def on_change(
        self,
        setting_id: str,
        callback: Callable[[Any], None]
    ) -> None:
        """
        Registers a callback for setting changes.

        Args:
            setting_id: Setting to watch
            callback: Function to call on change
        """
        self._registry.on_change(setting_id, callback)

    def _on_setting_changed(self, setting_id: str, value: Any) -> None:
        """Handles setting changes from registry."""
        self.SIG_SETTINGS_CHANGED.emit(setting_id, value)

        # Auto-save if enabled (could be made configurable)
        # self.save_settings()
