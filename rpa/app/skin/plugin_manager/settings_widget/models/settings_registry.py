"""
SettingsRegistry - Central storage and management for all settings.

The registry acts as the single source of truth for settings data,
providing methods for registration, retrieval, and change notification.
"""

from typing import Any, Callable, Dict, List, Optional, Set
from rpa.app.skin.plugin_manager.settings_widget.qt_compat import QObject, Signal

from rpa.app.skin.plugin_manager.settings_widget.models.setting_item import SettingItem, SettingType
from rpa.app.skin.plugin_manager.settings_widget.models.setting_category import SettingCategory


class SettingsRegistry(QObject):
    """
    Central registry for all application settings.

    Provides:
    - Setting registration and retrieval
    - Category management
    - Change notification via Qt signals
    - Search indexing

    Signals:
        SIG_SETTINGS_CHANGED: Emitted when any setting value changes (full_id, new_value)
        setting_registered: Emitted when a new setting is registered (full_id)
        category_added: Emitted when a new category is added (category_id)
    """

    # Qt Signals for change notifications
    SIG_SETTINGS_CHANGED = Signal(str, object)  # (setting_id, new_value)
    setting_registered = Signal(str)        # (setting_id)
    category_added = Signal(str)            # (category_id)

    def __init__(self, parent: Optional[QObject] = None):
        """
        Initializes the settings registry.

        Args:
            parent: Optional parent QObject
        """
        super().__init__(parent)

        # Storage containers
        self._settings: Dict[str, SettingItem] = {}
        self._categories: Dict[str, SettingCategory] = {}
        self._root_categories: List[SettingCategory] = []

        # Change callbacks (in addition to signals)
        self._change_callbacks: Dict[str, List[Callable]] = {}

        # Search index for fast lookups
        self._search_index: Dict[str, Set[str]] = {}

    def register_setting(self, setting: SettingItem) -> None:
        """
        Registers a new setting in the registry.

        Args:
            setting: The setting to register

        Raises:
            ValueError: If a setting with the same ID already exists
        """
        full_id = setting.full_id

        if full_id in self._settings:
            raise ValueError(f"Setting '{full_id}' is already registered")

        self._settings[full_id] = setting
        self._index_setting(setting)

        # Add to appropriate category
        self._add_to_category(setting)

        self.setting_registered.emit(full_id)

    def register_settings(
        self,
        settings: List[Dict[str, Any]],
        namespace: str = "",
        category: str = "General"
    ) -> None:
        """
        Batch registers multiple settings from dictionaries.

        Args:
            settings: List of setting configuration dictionaries
            namespace: Namespace to apply to all settings
            category: Default category for settings without one specified
        """
        for setting_data in settings:
            # Apply defaults
            setting_data.setdefault("namespace", namespace)
            setting_data.setdefault("category", category)

            setting = SettingItem.from_dict(setting_data)
            self.register_setting(setting)

    def get_setting(self, setting_id: str) -> Optional[SettingItem]:
        """
        Retrieves a setting by its full ID.

        Args:
            setting_id: Full ID of the setting (namespace.id)

        Returns:
            The setting if found, None otherwise
        """
        return self._settings.get(setting_id)

    def get_value(self, setting_id: str, default: Any = None) -> Any:
        """
        Gets the current value of a setting.

        Args:
            setting_id: Full ID of the setting
            default: Value to return if setting not found

        Returns:
            Current setting value or default
        """
        setting = self.get_setting(setting_id)
        if setting:
            return setting.get_value()
        return default

    def set_value(self, setting_id: str, value: Any) -> bool:
        """
        Sets the value of a setting.

        Args:
            setting_id: Full ID of the setting
            value: New value to set

        Returns:
            True if value was set successfully
        """
        setting = self.get_setting(setting_id)
        if setting and setting.set_value(value):
            self._emit_change(setting_id, value)
            return True
        return False

    def reset_setting(self, setting_id: str) -> None:
        """
        Resets a setting to its default value.

        Args:
            setting_id: Full ID of the setting to reset
        """
        setting = self.get_setting(setting_id)
        if setting:
            setting.reset_to_default()
            self._emit_change(setting_id, setting.get_value())

    def reset_all(self) -> None:
        """Resets all settings to their default values."""
        for setting_id, setting in self._settings.items():
            setting.reset_to_default()
            self._emit_change(setting_id, setting.get_value())

    def get_category(self, category_id: str) -> Optional[SettingCategory]:
        """
        Retrieves a category by its ID.

        Args:
            category_id: ID of the category

        Returns:
            The category if found, None otherwise
        """
        return self._categories.get(category_id)

    def get_root_categories(self) -> List[SettingCategory]:
        """Returns list of top-level categories."""
        return sorted(self._root_categories, key=lambda c: c.order)

    def get_all_settings(self) -> List[SettingItem]:
        """Returns all registered settings."""
        return list(self._settings.values())

    def get_modified_settings(self) -> List[SettingItem]:
        """Returns settings that have been changed from defaults."""
        return [s for s in self._settings.values() if s.is_modified()]

    def search(self, query: str) -> List[SettingItem]:
        """
        Searches settings by query string.

        Matches against title, description, ID, and tags.

        Args:
            query: Search query (case-insensitive)

        Returns:
            List of matching settings
        """
        if not query:
            return list(self._settings.values())

        query_lower = query.lower()
        query_terms = query_lower.split()

        matching_ids: Set[str] = set()

        # Search through index
        for term in query_terms:
            for indexed_term, setting_ids in self._search_index.items():
                if term in indexed_term:
                    matching_ids.update(setting_ids)

        # Also do direct substring matching on titles/descriptions
        for setting_id, setting in self._settings.items():
            if (query_lower in setting.title.lower() or
                query_lower in setting.description.lower() or
                query_lower in setting.id.lower()):
                matching_ids.add(setting_id)

        return [self._settings[sid] for sid in matching_ids if sid in self._settings]

    def on_change(self, setting_id: str, callback: Callable[[Any], None]) -> None:
        """
        Registers a callback for setting value changes.

        Args:
            setting_id: Full ID of the setting to watch
            callback: Function to call with new value
        """
        if setting_id not in self._change_callbacks:
            self._change_callbacks[setting_id] = []
        self._change_callbacks[setting_id].append(callback)

    def remove_change_callback(
        self,
        setting_id: str,
        callback: Callable[[Any], None]
    ) -> None:
        """
        Removes a previously registered change callback.

        Args:
            setting_id: Full ID of the setting
            callback: The callback to remove
        """
        if setting_id in self._change_callbacks:
            try:
                self._change_callbacks[setting_id].remove(callback)
            except ValueError:
                pass

    def to_dict(self) -> Dict[str, Any]:
        """
        Serializes all settings to a dictionary.

        Returns:
            Dictionary with all setting values
        """
        return {
            setting_id: setting.get_value()
            for setting_id, setting in self._settings.items()
        }

    def load_values(self, values: Dict[str, Any]) -> None:
        """
        Loads setting values from a dictionary.

        Args:
            values: Dictionary mapping setting IDs to values
        """
        for setting_id, value in values.items():
            if setting_id in self._settings:
                self._settings[setting_id].set_value(value)

    def _add_to_category(self, setting: SettingItem) -> None:
        """Adds a setting to its designated category, creating if needed."""
        category_path = setting.category.split(" > ")

        parent_category = None
        full_path = ""

        for i, cat_name in enumerate(category_path):
            full_path = " > ".join(category_path[:i + 1])
            category_id = f"{setting.namespace}.{full_path}" if setting.namespace else full_path

            if category_id not in self._categories:
                # Create new category
                new_category = SettingCategory(
                    id=category_id,
                    name=cat_name,
                    order=len(self._categories)
                )
                self._categories[category_id] = new_category

                if parent_category:
                    parent_category.add_subcategory(new_category)
                else:
                    self._root_categories.append(new_category)

                self.category_added.emit(category_id)

            parent_category = self._categories[category_id]

        # Add setting to the final category
        if parent_category:
            parent_category.add_setting(setting)

    def _index_setting(self, setting: SettingItem) -> None:
        """Adds setting to search index."""
        terms = set()

        # Index title words
        terms.update(setting.title.lower().split())

        # Index description words
        terms.update(setting.description.lower().split())

        # Index ID parts
        terms.update(setting.id.lower().split("_"))
        terms.update(setting.id.lower().split("-"))

        # Index namespace
        if setting.namespace:
            terms.add(setting.namespace.lower())

        # Index tags
        terms.update(tag.lower() for tag in setting.tags)

        # Add to index
        for term in terms:
            if term:  # Skip empty strings
                if term not in self._search_index:
                    self._search_index[term] = set()
                self._search_index[term].add(setting.full_id)

    def _emit_change(self, setting_id: str, value: Any) -> None:
        """Emits change notification via signal and callbacks."""
        self.SIG_SETTINGS_CHANGED.emit(setting_id, value)

        if setting_id in self._change_callbacks:
            for callback in self._change_callbacks[setting_id]:
                try:
                    callback(value)
                except Exception:
                    pass  # Don't let callback errors break the registry
