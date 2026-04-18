"""
Settings Widget - A VS Code-style settings UI for PySide applications.

This package provides a modular, extensible settings widget that supports:
- Plugin-based settings registration via API
- Multiple setting types (boolean, string, number, enum, etc.)
- Real-time search filtering
- Hierarchical category navigation
- Persistent storage

Compatible with both PySide2 and PySide6.
"""

from rpa.app.skin.plugin_manager.settings_widget.api.plugin_api import SettingsAPI
from rpa.app.skin.plugin_manager.settings_widget.views.settings_widget import SettingsWidget

__version__ = "1.0.0"
__all__ = ["SettingsAPI", "SettingsWidget"]
