"""
SettingsPanel - Right panel displaying settings editors.

Shows the settings for the currently selected category with
their respective editor widgets.
"""

from typing import Dict, List, Optional

from rpa.app.plugin_manager.settings_widget.qt_compat import (
    QWidget,
    QVBoxLayout,
    QScrollArea,
    QLabel,
    QFrame,
    Signal,
    QSizePolicy,
    Qt,
)
from rpa.app.plugin_manager.settings_widget.models.setting_item import SettingItem
from rpa.app.plugin_manager.settings_widget.models.setting_category import SettingCategory
from rpa.app.plugin_manager.settings_widget.views.editors.base_editor import BaseEditor
from rpa.app.plugin_manager.settings_widget.views.editors.editor_factory import EditorFactory


class SettingsPanel(QWidget):
    """
    Panel displaying settings editors for a category.

    Features:
    - Scrollable list of settings
    - Category headers
    - Search result highlighting
    - Editor creation via factory

    Signals:
        SIG_SETTINGS_CHANGED: Emitted when any setting value changes (setting_id, value)
    """

    SIG_SETTINGS_CHANGED = Signal(str, object)  # (setting_id, new_value)

    def __init__(self, parent: Optional[QWidget] = None):
        """
        Initializes the settings panel.

        Args:
            parent: Optional parent widget
        """
        super().__init__(parent)
        self._editors: Dict[str, BaseEditor] = {}
        self._current_category: Optional[str] = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Creates the settings panel UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Scroll area for settings
        self._scroll_area = QScrollArea()
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        main_layout.addWidget(self._scroll_area)

        # Container widget for scroll area
        self._container = QWidget()
        self._container.setStyleSheet("background: #1e1e1e;")
        self._container_layout = QVBoxLayout(self._container)
        self._container_layout.setContentsMargins(16, 8, 16, 8)
        self._container_layout.setSpacing(0)

        self._scroll_area.setWidget(self._container)

    def display_category(self, category: SettingCategory) -> None:
        """
        Displays all settings for a category.

        Args:
            category: The category to display
        """
        self._clear_editors()
        self._current_category = category.id

        # Add category header
        header = self._create_category_header(category)
        self._container_layout.addWidget(header)

        # Add settings from this category
        for setting in category.settings:
            editor = self._create_editor(setting)
            self._container_layout.addWidget(editor)
            self._add_separator()

        # Add subcategories
        for subcategory in category.subcategories:
            self._add_subcategory(subcategory)

        # Add stretch at end
        self._container_layout.addStretch()

    def display_settings(self, settings: List[SettingItem]) -> None:
        """
        Displays a flat list of settings (e.g., search results).

        Args:
            settings: List of settings to display
        """
        self._clear_editors()
        self._current_category = None

        if not settings:
            # Show "no results" message
            no_results = QLabel("No settings found")
            no_results.setStyleSheet("""
                color: #888888;
                font-size: 14px;
                padding: 32px;
            """)
            self._container_layout.addWidget(no_results)
            self._container_layout.addStretch()
            return

        # Group settings by category for organized display
        categories: Dict[str, List[SettingItem]] = {}
        for setting in settings:
            cat_key = f"{setting.namespace}.{setting.category}" if setting.namespace else setting.category
            if cat_key not in categories:
                categories[cat_key] = []
            categories[cat_key].append(setting)

        # Display grouped settings
        for cat_key, cat_settings in categories.items():
            # Category header
            header = QLabel(cat_key.replace(".", " > "))
            header.setStyleSheet("""
                color: #569cd6;
                font-size: 11px;
                font-weight: bold;
                padding: 16px 0 8px 0;
                text-transform: uppercase;
                letter-spacing: 1px;
            """)
            self._container_layout.addWidget(header)

            # Settings in this category
            for setting in cat_settings:
                editor = self._create_editor(setting)
                self._container_layout.addWidget(editor)
                self._add_separator()

        self._container_layout.addStretch()

    def _create_category_header(self, category: SettingCategory) -> QWidget:
        """Creates a header widget for a category."""
        header = QWidget()
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 16)
        header_layout.setSpacing(4)

        # Category name
        name_label = QLabel(category.name)
        name_label.setStyleSheet("""
            color: #ffffff;
            font-size: 20px;
            font-weight: bold;
        """)
        header_layout.addWidget(name_label)

        # Category description
        if category.description:
            desc_label = QLabel(category.description)
            desc_label.setStyleSheet("color: #888888; font-size: 13px;")
            desc_label.setWordWrap(True)
            header_layout.addWidget(desc_label)

        return header

    def _add_subcategory(self, category: SettingCategory) -> None:
        """Adds a subcategory section."""
        if not category.has_settings():
            return

        # Subcategory header
        header = QLabel(category.name)
        header.setStyleSheet("""
            color: #569cd6;
            font-size: 16px;
            font-weight: bold;
            padding: 24px 0 8px 0;
        """)
        self._container_layout.addWidget(header)

        # Settings
        for setting in category.settings:
            editor = self._create_editor(setting)
            self._container_layout.addWidget(editor)
            self._add_separator()

        # Nested subcategories
        for sub in category.subcategories:
            self._add_subcategory(sub)

    def _create_editor(self, setting: SettingItem) -> BaseEditor:
        """Creates an editor widget for a setting."""
        editor = EditorFactory.create_editor(setting, self._container)
        editor.value_changed.connect(
            lambda value, s=setting: self._on_editor_changed(s.full_id, value)
        )
        self._editors[setting.full_id] = editor
        return editor

    def _add_separator(self) -> None:
        """Adds a visual separator between settings."""
        separator = QFrame()
        separator.setFixedHeight(1)
        separator.setStyleSheet("background: #3c3c3c;")
        self._container_layout.addWidget(separator)

    def _on_editor_changed(self, setting_id: str, value: object) -> None:
        """Handles editor value changes."""
        self.SIG_SETTINGS_CHANGED.emit(setting_id, value)

    def _clear_editors(self) -> None:
        """Removes all editor widgets."""
        self._editors.clear()

        # Clear container layout
        while self._container_layout.count():
            item = self._container_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def get_editor(self, setting_id: str) -> Optional[BaseEditor]:
        """
        Gets an editor by setting ID.

        Args:
            setting_id: Full ID of the setting

        Returns:
            The editor widget if found
        """
        return self._editors.get(setting_id)

    def scroll_to_setting(self, setting_id: str) -> None:
        """
        Scrolls to make a specific setting visible.

        Args:
            setting_id: Full ID of the setting
        """
        editor = self._editors.get(setting_id)
        if editor:
            self._scroll_area.ensureWidgetVisible(editor)

    def highlight_setting(self, setting_id: str) -> None:
        """
        Highlights a setting temporarily.

        Args:
            setting_id: Full ID of the setting
        """
        editor = self._editors.get(setting_id)
        if editor:
            self.scroll_to_setting(setting_id)

    def get_current_category_id(self) -> str:
        """
        Gets the current category id from Settings Panel.

        Returns:
            A category ID consisting of setting namespace.category
        """
        return self._current_category
