"""
SettingsAPI - Public API for plugin settings integration.

Provides a simple, static interface for plugins to register
and access settings without direct access to internal components.
"""

from typing import Any, Callable, Dict, List, Optional

from rpa.app.skin.plugin_manager.settings_widget.models.settings_registry import SettingsRegistry
from rpa.app.skin.plugin_manager.settings_widget.models.setting_item import SettingItem, SettingType
from rpa.app.skin.plugin_manager.settings_widget.controllers.settings_controller import SettingsController
from rpa.app.skin.plugin_manager.settings_widget.storage.settings_storage import SettingsStorage


class SettingsAPI:
    """
    Static API for plugin settings integration.

    Provides a singleton-like interface for plugins to:
    - Register their settings
    - Get/set setting values
    - Listen for changes
    - Load/save settings

    Usage:
        from settings_widget import SettingsAPI

        # Register settings
        SettingsAPI.register_settings(
            category="My Plugin",
            namespace="myPlugin",
            settings=[
                {
                    "id": "enableFeature",
                    "type": "boolean",
                    "default": True,
                    "title": "Enable Feature",
                    "description": "Controls whether the feature is enabled."
                }
            ]
        )

        # Get/set values
        value = SettingsAPI.get_value("myPlugin.enableFeature")
        SettingsAPI.set_value("myPlugin.enableFeature", False)

        # Listen for changes
        SettingsAPI.on_change("myPlugin.enableFeature", my_callback)
    """

    # Singleton instances
    _registry: Optional[SettingsRegistry] = None
    _controller: Optional[SettingsController] = None
    _storage: Optional[SettingsStorage] = None
    _initialized: bool = False

    @classmethod
    def initialize(
        cls,
        registry: Optional[SettingsRegistry] = None,
        storage: Optional[SettingsStorage] = None,
        auto_load: bool = True
    ) -> None:
        """
        Initializes the settings API.

        Should be called once at application startup before plugins load.

        Args:
            registry: Custom registry (creates new if None)
            storage: Custom storage backend (creates new if None)
            auto_load: Whether to load settings from storage
        """
        cls._registry = registry or SettingsRegistry()
        cls._storage = storage or SettingsStorage()
        cls._controller = SettingsController(cls._registry, cls._storage)

        if auto_load and cls._storage.exists():
            cls._controller.load_settings()

        cls._initialized = True

    @classmethod
    def _ensure_initialized(cls) -> None:
        """Ensures the API is initialized."""
        if not cls._initialized:
            cls.initialize()

    @classmethod
    def get_registry(cls) -> SettingsRegistry:
        """
        Returns the settings registry.

        Useful for creating SettingsWidget instances.

        Returns:
            The shared settings registry
        """
        cls._ensure_initialized()
        return cls._registry

    @classmethod
    def get_controller(cls) -> SettingsController:
        """
        Returns the settings controller.

        Returns:
            The shared settings controller
        """
        cls._ensure_initialized()
        return cls._controller

    @classmethod
    def register_settings(
        cls,
        namespace: str,
        category: str,
        settings: List[Dict[str, Any]]
    ) -> None:
        """
        Registers multiple settings from a plugin.

        Args:
            settings: List of setting configurations
            namespace: Plugin namespace (prefix for all setting IDs)
            category: Default category for settings

        Example:
            SettingsAPI.register_settings(
                namespace="git",
                category="Extensions > Git",
                settings=[
                    {
                        "id": "enableSmartCommit",
                        "type": "boolean",
                        "default": False,
                        "title": "Enable Smart Commit",
                        "description": "Commit all changes when there are no staged changes."
                    },
                    {
                        "id": "autofetch",
                        "type": "enum",
                        "default": "false",
                        "options": ["false", "true", "all"],
                        "title": "Autofetch",
                        "description": "When enabled, fetch all remotes automatically."
                    }
                ]
            )
        """
        cls._ensure_initialized()
        cls._controller.register_settings(settings, namespace, category)

    @classmethod
    def register_setting(
        cls,
        setting_id: str,
        setting_type: str,
        default: Any,
        title: str,
        description: str = "",
        namespace: str = "",
        category: str = "General",
        **kwargs
    ) -> None:
        """
        Registers a single setting.

        Args:
            setting_id: Unique ID for the setting
            setting_type: Type name (boolean, string, integer, etc.)
            default: Default value
            title: Display title
            description: Description text
            namespace: Plugin namespace
            category: Category path
            **kwargs: Additional setting options
        """
        cls._ensure_initialized()

        setting_data = {
            "id": setting_id,
            "type": setting_type,
            "default": default,
            "title": title,
            "description": description,
            "namespace": namespace,
            "category": category,
            **kwargs
        }

        setting = SettingItem.from_dict(setting_data)
        cls._controller.register_setting(setting)

    @classmethod
    def get_value(cls, setting_id: str, default: Any = None) -> Any:
        """
        Gets a setting value.

        Args:
            setting_id: Full ID (namespace.id) of the setting
            default: Value to return if setting not found

        Returns:
            Current setting value
        """
        cls._ensure_initialized()
        return cls._controller.get_value(setting_id, default)

    @classmethod
    def set_value(cls, setting_id: str, value: Any) -> bool:
        """
        Sets a setting value.

        Args:
            setting_id: Full ID (namespace.id) of the setting
            value: New value to set

        Returns:
            True if value was set successfully
        """
        cls._ensure_initialized()
        return cls._controller.set_value(setting_id, value)

    @classmethod
    def reset_setting(cls, setting_id: str) -> None:
        """
        Resets a setting to its default value.

        Args:
            setting_id: Full ID of the setting
        """
        cls._ensure_initialized()
        cls._controller.reset_setting(setting_id)

    @classmethod
    def reset_all(cls) -> None:
        """Resets all settings to their defaults."""
        cls._ensure_initialized()
        cls._controller.reset_all()

    @classmethod
    def on_change(
        cls,
        setting_id: str,
        callback: Callable[[Any], None]
    ) -> None:
        """
        Registers a callback for setting value changes.

        Args:
            setting_id: Setting to watch
            callback: Function to call with new value

        Example:
            def on_theme_changed(value):
                print(f"Theme changed to: {value}")

            SettingsAPI.on_change("app.theme", on_theme_changed)
        """
        cls._ensure_initialized()
        cls._controller.on_change(setting_id, callback)

    @classmethod
    def save(cls, path: Optional[str] = None) -> bool:
        """
        Saves all settings to storage.

        Args:
            path: Optional custom file path

        Returns:
            True if save was successful
        """
        cls._ensure_initialized()
        return cls._controller.save_settings(path)

    @classmethod
    def load(cls, path: Optional[str] = None) -> bool:
        """
        Loads settings from storage.

        Args:
            path: Optional custom file path

        Returns:
            True if load was successful
        """
        cls._ensure_initialized()
        return cls._controller.load_settings(path)

    @classmethod
    def get_all_values(cls) -> Dict[str, Any]:
        """
        Returns all setting values as a dictionary.

        Returns:
            Dictionary mapping setting IDs to values
        """
        cls._ensure_initialized()
        return cls._registry.to_dict()

    @classmethod
    def search(cls, query: str) -> List[SettingItem]:
        """
        Searches settings by query.

        Args:
            query: Search string

        Returns:
            List of matching settings
        """
        cls._ensure_initialized()
        return cls._controller.search(query)
