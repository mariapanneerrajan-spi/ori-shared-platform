"""
SettingCategory - Groups related settings together.

Categories provide hierarchical organization for the settings sidebar
and help users navigate large numbers of settings.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field

from itview.skin.plugin_manager.settings_widget.models.setting_item import SettingItem


@dataclass
class SettingCategory:
    """
    Represents a category/group of related settings.

    Categories can be nested to create a hierarchy (e.g., Extensions > Git).

    Attributes:
        id: Unique identifier for the category
        name: Display name shown in sidebar
        description: Optional description for the category
        icon: Optional icon name/path for sidebar display
        parent_id: ID of parent category for nesting (None for root)
        order: Sort order within parent (lower = higher)
        settings: List of settings in this category
        subcategories: Nested child categories
    """
    id: str
    name: str
    description: str = ""
    icon: str = ""
    parent_id: Optional[str] = None
    order: int = 0
    settings: List[SettingItem] = field(default_factory=list)
    subcategories: List["SettingCategory"] = field(default_factory=list)

    def add_setting(self, setting: SettingItem) -> None:
        """
        Adds a setting to this category.

        Args:
            setting: The setting item to add
        """
        # Avoid duplicates
        if not any(s.full_id == setting.full_id for s in self.settings):
            self.settings.append(setting)

    def remove_setting(self, setting_id: str) -> bool:
        """
        Removes a setting by ID.

        Args:
            setting_id: Full ID of the setting to remove

        Returns:
            True if setting was found and removed
        """
        for i, setting in enumerate(self.settings):
            if setting.full_id == setting_id:
                self.settings.pop(i)
                return True
        return False

    def get_setting(self, setting_id: str) -> Optional[SettingItem]:
        """
        Finds a setting by its ID.

        Args:
            setting_id: Full ID or local ID of the setting

        Returns:
            The setting if found, None otherwise
        """
        for setting in self.settings:
            if setting.full_id == setting_id or setting.id == setting_id:
                return setting
        return None

    def add_subcategory(self, category: "SettingCategory") -> None:
        """
        Adds a nested subcategory.

        Args:
            category: The subcategory to add
        """
        category.parent_id = self.id
        if not any(c.id == category.id for c in self.subcategories):
            self.subcategories.append(category)
            self.subcategories.sort(key=lambda c: c.order)

    def get_subcategory(self, category_id: str) -> Optional["SettingCategory"]:
        """
        Finds a subcategory by ID.

        Args:
            category_id: ID of the subcategory

        Returns:
            The subcategory if found, None otherwise
        """
        for category in self.subcategories:
            if category.id == category_id:
                return category
        return None

    def get_all_settings(self) -> List[SettingItem]:
        """
        Returns all settings including those in subcategories.

        Returns:
            Flattened list of all settings
        """
        all_settings = list(self.settings)
        for subcategory in self.subcategories:
            all_settings.extend(subcategory.get_all_settings())
        return all_settings

    def get_modified_settings(self) -> List[SettingItem]:
        """
        Returns only settings that have been modified from defaults.

        Returns:
            List of modified settings
        """
        return [s for s in self.get_all_settings() if s.is_modified()]

    def has_settings(self) -> bool:
        """Returns True if category or subcategories contain settings."""
        if self.settings:
            return True
        return any(sub.has_settings() for sub in self.subcategories)

    def to_dict(self) -> Dict:
        """Serializes the category to a dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "icon": self.icon,
            "parent_id": self.parent_id,
            "order": self.order,
            "settings": [s.to_dict() for s in self.settings],
            "subcategories": [c.to_dict() for c in self.subcategories],
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "SettingCategory":
        """
        Creates a SettingCategory from a dictionary.

        Args:
            data: Dictionary with category configuration

        Returns:
            New SettingCategory instance
        """
        category = cls(
            id=data["id"],
            name=data.get("name", data["id"]),
            description=data.get("description", ""),
            icon=data.get("icon", ""),
            parent_id=data.get("parent_id"),
            order=data.get("order", 0),
        )

        # Load settings
        for setting_data in data.get("settings", []):
            category.add_setting(SettingItem.from_dict(setting_data))

        # Load subcategories recursively
        for sub_data in data.get("subcategories", []):
            category.add_subcategory(cls.from_dict(sub_data))

        return category
