"""
CategoryTree - Left sidebar navigation for settings categories.

Displays a hierarchical tree of setting categories that users can
click to navigate to specific sections.
"""

from typing import Dict, List, Optional

from itview.skin.plugin_manager.settings_widget.qt_compat import (
    QWidget,
    QVBoxLayout,
    QTreeWidget,
    QTreeWidgetItem,
    QLabel,
    QHeaderView,
    Signal,
    Qt,
    QFont,
)
from itview.skin.plugin_manager.settings_widget.models.setting_category import SettingCategory


class CategoryTree(QWidget):
    """
    Tree widget displaying settings categories.

    Features:
    - Hierarchical category display
    - Expandable/collapsible sections
    - Selection highlighting
    - Category count badges

    Signals:
        category_selected: Emitted when a category is clicked (category_id)
    """

    category_selected = Signal(str)  # Emits category ID

    def __init__(self, parent: Optional[QWidget] = None):
        """
        Initializes the category tree.

        Args:
            parent: Optional parent widget
        """
        super().__init__(parent)
        self._category_items: Dict[str, QTreeWidgetItem] = {}
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Creates the category tree UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Tree widget
        self._tree = QTreeWidget()
        self._tree.setHeaderHidden(True)
        self._tree.setIndentation(16)
        self._tree.setAnimated(True)
        self._tree.setExpandsOnDoubleClick(True)
        self._tree.setStyleSheet("""
            QTreeWidget {
                background: #252526;
                border: none;
                color: #cccccc;
                font-size: 13px;
            }
            QTreeWidget::item {
                padding: 8px 12px;
                border: none;
            }
            QTreeWidget::item:hover {
                background: #2a2d2e;
            }
            QTreeWidget::item:selected {
                background: #094771;
            }
            QTreeWidget::branch {
                background: #252526;
            }
            QTreeWidget::branch:has-children:!has-siblings:closed,
            QTreeWidget::branch:closed:has-children:has-siblings {
                image: none;
                border-image: none;
            }
            QTreeWidget::branch:open:has-children:!has-siblings,
            QTreeWidget::branch:open:has-children:has-siblings {
                image: none;
                border-image: none;
            }
        """)
        self._tree.itemClicked.connect(self._on_item_clicked)
        self._tree.itemExpanded.connect(self._on_item_expanded)
        layout.addWidget(self._tree)

    def set_categories(self, categories: List[SettingCategory]) -> None:
        """
        Populates the tree with categories.

        Args:
            categories: List of root-level categories
        """
        self._tree.clear()
        self._category_items.clear()

        for category in categories:
            self._add_category_item(category, None)

        # Expand all by default
        self._tree.expandAll()

    def _add_category_item(
        self,
        category: SettingCategory,
        parent_item: Optional[QTreeWidgetItem]
    ) -> QTreeWidgetItem:
        """
        Adds a category as a tree item.

        Args:
            category: The category to add
            parent_item: Parent tree item (None for root)

        Returns:
            The created tree item
        """
        if parent_item is None:
            item = QTreeWidgetItem(self._tree)
        else:
            item = QTreeWidgetItem(parent_item)

        # Set display text with setting count
        setting_count = len(category.get_all_settings())
        display_text = category.name
        if setting_count > 0:
            display_text = f"{category.name}"

        item.setText(0, display_text)
        item.setData(0, Qt.UserRole, category.id)

        # Store reference
        self._category_items[category.id] = item

        # Add subcategories
        for subcategory in category.subcategories:
            self._add_category_item(subcategory, item)

        return item

    def _on_item_clicked(self, item: QTreeWidgetItem, column: int) -> None:
        """Handles category item clicks."""
        category_id = item.data(0, Qt.UserRole)
        if category_id:
            self.category_selected.emit(category_id)

    def _on_item_expanded(self, item: QTreeWidgetItem) -> None:
        """Handles category expansion."""
        pass  # Could be used for lazy loading

    def select_category(self, category_id: str) -> None:
        """
        Selects and scrolls to a category.

        Args:
            category_id: ID of the category to select
        """
        item = self._category_items.get(category_id)
        if item:
            self._tree.setCurrentItem(item)
            self._tree.scrollToItem(item)

    def expand_all(self) -> None:
        """Expands all categories."""
        self._tree.expandAll()

    def collapse_all(self) -> None:
        """Collapses all categories."""
        self._tree.collapseAll()

    def update_category(self, category: SettingCategory) -> None:
        """
        Updates a single category's display.

        Args:
            category: The category to update
        """
        item = self._category_items.get(category.id)
        if item:
            setting_count = len(category.get_all_settings())
            item.setText(0, f"{category.name}")

    def filter_categories(self, visible_ids: List[str]) -> None:
        """
        Shows only categories with the given IDs.

        Args:
            visible_ids: List of category IDs to show
        """
        for category_id, item in self._category_items.items():
            # Show if this category or any parent is in visible list
            should_show = category_id in visible_ids
            item.setHidden(not should_show)
            item.setSelected(not should_show)

            # Ensure parents are visible
            if should_show:
                parent = item.parent()
                while parent:
                    parent.setHidden(False)
                    parent = parent.parent()

    def show_all_categories(self) -> None:
        """Shows all categories (removes filter)."""
        for item in self._category_items.values():
            item.setHidden(False)
