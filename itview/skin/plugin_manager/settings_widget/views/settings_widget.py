"""
SettingsWidget - Main composite settings widget.

Combines SearchBar, CategoryTree, and SettingsPanel into a complete
settings interface similar to VS Code. Includes integrated header bar
with title and reset functionality.
"""

from typing import Optional

from itview.skin.plugin_manager.settings_widget.qt_compat import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QSplitter,
    QPushButton,
    QLabel,
    QMessageBox,
    QTimer,
    Signal,
    Qt,
)
from itview.skin.plugin_manager.settings_widget.views.search_bar import SearchBar
from itview.skin.plugin_manager.settings_widget.views.category_tree import CategoryTree
from itview.skin.plugin_manager.settings_widget.views.settings_panel import SettingsPanel
from itview.skin.plugin_manager.settings_widget.models.settings_registry import SettingsRegistry


class SettingsWidget(QWidget):
    """
    Main settings widget combining all UI components.

    Layout:
    ┌─────────────────────────────────────────┐
    │       Header (Title + Reset Button)     │
    ├─────────────────────────────────────────┤
    │            Search Bar                   │
    ├────────────┬────────────────────────────┤
    │            │                            │
    │  Category  │      Settings Panel        │
    │    Tree    │                            │
    │            │                            │
    ├────────────┴────────────────────────────┤

    Features:
    - Integrated header with title and reset button
    - Real-time search filtering
    - Category navigation
    - Synchronized view updates

    Signals:
        SIG_SETTINGS_CHANGED: Emitted when any setting value changes
    """

    SIG_SETTINGS_CHANGED = Signal(str, object)  # (setting_id, new_value)

    def __init__(
        self,
        registry: Optional[SettingsRegistry] = None,
        title: str = "Settings",
        parent: Optional[QWidget] = None
    ):
        """
        Initializes the settings widget.

        Args:
            registry: Settings registry to use (creates new if None)
            title: Title displayed in the header bar
            parent: Optional parent widget
        """
        super().__init__(parent)
        self._registry = registry or SettingsRegistry()
        self._title = title
        self._setup_ui()
        self._connect_signals()
        self._refresh_view()

    @property
    def registry(self) -> SettingsRegistry:
        """Returns the settings registry."""
        return self._registry

    def _setup_ui(self) -> None:
        """Creates the main widget UI."""
        self.setStyleSheet("""
            SettingsWidget {
                background: #1e1e1e;
            }
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Header bar
        self._header = self._create_header()
        main_layout.addWidget(self._header)

        # Search bar at top (compact)
        self._search_bar = SearchBar(self)
        self._search_bar.setFixedHeight(40)
        self._search_bar.setStyleSheet("background: #252526;")
        main_layout.addWidget(self._search_bar)

        # Splitter for sidebar and content
        self._splitter = QSplitter(Qt.Horizontal)
        self._splitter.setStyleSheet("""
            QSplitter::handle {
                background: #3c3c3c;
                width: 1px;
            }
        """)

        # Category tree (left sidebar)
        self._category_tree = CategoryTree(self)
        self._category_tree.setMinimumWidth(200)
        self._category_tree.setMaximumWidth(350)
        self._splitter.addWidget(self._category_tree)

        # Settings panel (right content)
        self._settings_panel = SettingsPanel(self)
        self._splitter.addWidget(self._settings_panel)

        # Set initial splitter sizes (25% / 75%)
        self._splitter.setSizes([250, 750])

        main_layout.addWidget(self._splitter)

    def _create_header(self) -> QWidget:
        """Creates the header bar with title and reset button."""
        header = QWidget()
        header.setFixedHeight(40)
        header.setStyleSheet("background: #333333;")

        layout = QHBoxLayout(header)
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(8)

        # Title label
        title_label = QLabel(f"{self._title}")
        title_label.setStyleSheet(
            "color: white; font-size: 14px; font-weight: bold;"
        )
        layout.addWidget(title_label)

        layout.addStretch()

        # Reset button
        self._reset_btn = QPushButton("Reset All")
        self._reset_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #cccccc;
                border: 1px solid #5a5a5a;
                padding: 4px 12px;
                border-radius: 3px;
                font-size: 12px;
            }
            QPushButton:hover {
                background: #4a4a4a;
            }
        """)
        self._reset_btn.clicked.connect(self._on_reset_clicked)
        layout.addWidget(self._reset_btn)

        return header

    def _on_reset_clicked(self) -> None:
        """Handles reset button click with confirmation dialog."""
        reply = QMessageBox.question(
            self,
            "Reset Settings",
            "Are you sure you want to reset all settings to their defaults?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.reset_all_settings()

    def _connect_signals(self) -> None:
        """Connects internal signals."""
        # Search bar
        self._search_bar.search_changed.connect(self._on_search)

        # Category tree
        self._category_tree.category_selected.connect(self._on_category_selected)

        # Settings panel
        self._settings_panel.SIG_SETTINGS_CHANGED.connect(self._on_setting_changed)

        # Registry
        self._registry.setting_registered.connect(self._on_setting_registered)
        self._registry.category_added.connect(self._on_category_added)
        self._registry.SIG_SETTINGS_CHANGED.connect(self.SIG_SETTINGS_CHANGED)

    def _refresh_view(self) -> None:
        """Refreshes the entire view from registry."""
        categories = self._registry.get_root_categories()
        self._category_tree.set_categories(categories)

        if categories:
            current_category_id = self._settings_panel.get_current_category_id()
            if current_category_id:
                self._on_category_selected(current_category_id)
            else:
                self._show_category(categories[0].id)

    def _on_search(self, query: str) -> None:
        """Handles search query changes."""
        if query:
            # Search mode - show matching settings
            results = self._registry.search(query)
            self._settings_panel.display_settings(results)

            # Update result count
            total = len(self._registry.get_all_settings())
            self._search_bar.set_result_count(len(results), total)

            # Filter category tree to show relevant categories
            visible_cats = set()
            for setting in results:
                cat_id = f"{setting.namespace}.{setting.category}" if setting.namespace else setting.category
                visible_cats.add(cat_id)
            self._category_tree.filter_categories(list(visible_cats))
        else:
            # Normal mode - show categories
            self._category_tree.show_all_categories()
            self._refresh_view()

    def _on_category_selected(self, category_id: str) -> None:
        """Handles category selection."""
        # Clear search when selecting category
        if self._search_bar.get_query():
            self._search_bar.clear()
        self._show_category(category_id)

    def _show_category(self, category_id: str) -> None:
        """Displays a category's settings."""
        category = self._registry.get_category(category_id)
        if category:
            self._settings_panel.display_category(category)
            self._category_tree.select_category(category_id)

    def _on_setting_changed(self, setting_id: str, value: object) -> None:
        """Handles setting value changes from panel."""
        self._registry.set_value(setting_id, value)

    def _on_setting_registered(self, setting_id: str) -> None:
        """Handles new setting registration."""
        self._refresh_view()

    def _on_category_added(self, category_id: str) -> None:
        """Handles new category addition."""
        categories = self._registry.get_root_categories()
        self._category_tree.set_categories(categories)

    def focus_search(self) -> None:
        """Sets focus to the search bar."""
        self._search_bar.focus()

    def select_setting(self, setting_id: str) -> None:
        """
        Selects and scrolls to a specific setting.

        Args:
            setting_id: Full ID of the setting
        """
        setting = self._registry.get_setting(setting_id)
        if setting:
            # Navigate to category
            cat_id = f"{setting.namespace}.{setting.category}" if setting.namespace else setting.category
            self._show_category(cat_id)

            # Scroll to and highlight setting
            self._settings_panel.scroll_to_setting(setting_id)
            self._settings_panel.highlight_setting(setting_id)

    def reset_all_settings(self) -> None:
        """Resets all settings to defaults."""
        self._registry.reset_all()
        self._refresh_view()

    def get_value(self, setting_id: str) -> object:
        """
        Gets a setting value.

        Args:
            setting_id: Full ID of the setting

        Returns:
            The current setting value
        """
        return self._registry.get_value(setting_id)

    def set_value(self, setting_id: str, value: object) -> None:
        """
        Sets a setting value.

        Args:
            setting_id: Full ID of the setting
            value: New value to set
        """
        self._registry.set_value(setting_id, value)

        # Update editor if visible
        editor = self._settings_panel.get_editor(setting_id)
        if editor:
            editor.set_value(value)
