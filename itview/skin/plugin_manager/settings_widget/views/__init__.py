"""
Views package for UI components.

Contains:
- SettingsWidget: Main composite settings widget
- SearchBar: Search input with filtering
- CategoryTree: Left sidebar navigation
- SettingsPanel: Right panel displaying settings
- editors/: Individual setting editor widgets
"""

from itview.skin.plugin_manager.settings_widget.views.settings_widget import SettingsWidget
from itview.skin.plugin_manager.settings_widget.views.search_bar import SearchBar
from itview.skin.plugin_manager.settings_widget.views.category_tree import CategoryTree
from itview.skin.plugin_manager.settings_widget.views.settings_panel import SettingsPanel

__all__ = ["SettingsWidget", "SearchBar", "CategoryTree", "SettingsPanel"]
