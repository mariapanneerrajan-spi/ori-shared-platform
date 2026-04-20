"""
ArrayEditor - List editor for array/list settings.
"""

from typing import Any, List, Optional

from rpa.app.plugin_manager.settings_widget.qt_compat import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QListWidget,
    QListWidgetItem,
)
from rpa.app.plugin_manager.settings_widget.views.editors.base_editor import BaseEditor
from rpa.app.plugin_manager.settings_widget.models.setting_item import SettingItem


class ArrayEditor(BaseEditor):
    """
    Editor for array settings using a list widget.

    Displays a list of items with add/remove functionality.
    """

    def __init__(
        self,
        setting: SettingItem,
        parent: Optional[QWidget] = None
    ):
        """
        Initializes the array editor.

        Args:
            setting: The array setting to edit
            parent: Optional parent widget
        """
        super().__init__(setting, parent)

    def _setup_editor(self) -> None:
        """Creates the list widget with add/remove controls."""
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(4)

        # Input row for adding new items
        input_row = QHBoxLayout()
        input_row.setSpacing(4)

        self._input_field = QLineEdit()
        self._input_field.setPlaceholderText("Enter item and press Add")
        self._input_field.setStyleSheet("""
            QLineEdit {
                background: #3c3c3c;
                border: 1px solid #5a5a5a;
                border-radius: 3px;
                padding: 6px 10px;
                color: #cccccc;
                font-size: 13px;
            }
        """)
        self._input_field.returnPressed.connect(self._add_item)
        input_row.addWidget(self._input_field)

        self._add_button = QPushButton("Add")
        self._add_button.setStyleSheet("""
            QPushButton {
                background: #0e639c;
                border: none;
                border-radius: 3px;
                padding: 6px 16px;
                color: white;
                font-size: 13px;
            }
            QPushButton:hover {
                background: #1177bb;
            }
            QPushButton:pressed {
                background: #0d5a8c;
            }
        """)
        self._add_button.clicked.connect(self._add_item)
        input_row.addWidget(self._add_button)

        container_layout.addLayout(input_row)

        # List widget displaying items
        self._list_widget = QListWidget()
        self._list_widget.setMinimumHeight(100)
        self._list_widget.setMaximumHeight(200)
        self._list_widget.setStyleSheet("""
            QListWidget {
                background: #3c3c3c;
                border: 1px solid #5a5a5a;
                border-radius: 3px;
                color: #cccccc;
                font-size: 13px;
            }
            QListWidget::item {
                padding: 6px;
                border-bottom: 1px solid #4a4a4a;
            }
            QListWidget::item:selected {
                background: #094771;
            }
            QListWidget::item:hover {
                background: #4a4a4a;
            }
        """)
        container_layout.addWidget(self._list_widget)

        # Remove button
        remove_row = QHBoxLayout()
        remove_row.addStretch()

        self._remove_button = QPushButton("Remove Selected")
        self._remove_button.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: 1px solid #5a5a5a;
                border-radius: 3px;
                padding: 4px 12px;
                color: #cccccc;
                font-size: 12px;
            }
            QPushButton:hover {
                background: #4a4a4a;
                border-color: #6a6a6a;
            }
        """)
        self._remove_button.clicked.connect(self._remove_selected)
        remove_row.addWidget(self._remove_button)

        container_layout.addLayout(remove_row)

        self._editor_layout.addWidget(container)
        self._editor_layout.addStretch()

    def _load_value(self) -> None:
        """Loads the current value into the list widget."""
        self._list_widget.clear()
        value = self._setting.get_value()

        if isinstance(value, list):
            for item in value:
                self._list_widget.addItem(str(item))

    def get_value(self) -> List[str]:
        """Returns the current list of items."""
        items = []
        for i in range(self._list_widget.count()):
            item = self._list_widget.item(i)
            if item:
                items.append(item.text())
        return items

    def _add_item(self) -> None:
        """Adds a new item from the input field."""
        text = self._input_field.text().strip()
        if text:
            self._list_widget.addItem(text)
            self._input_field.clear()
            self._on_value_changed()

    def _remove_selected(self) -> None:
        """Removes the currently selected item."""
        current_row = self._list_widget.currentRow()
        if current_row >= 0:
            self._list_widget.takeItem(current_row)
            self._on_value_changed()
