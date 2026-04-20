"""
Models package for settings data structures.

Contains:
- SettingItem: Individual setting data model
- SettingCategory: Category/group of settings
- SettingsRegistry: Central settings storage and management
"""

from rpa.app.plugin_manager.settings_widget.models.setting_item import SettingItem, SettingType
from rpa.app.plugin_manager.settings_widget.models.setting_category import SettingCategory
from rpa.app.plugin_manager.settings_widget.models.settings_registry import SettingsRegistry

__all__ = ["SettingItem", "SettingType", "SettingCategory", "SettingsRegistry"]
