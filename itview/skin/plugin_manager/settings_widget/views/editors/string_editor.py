"""
StringEditor - Text input editor for string settings.
"""

from typing import Any, Optional

from itview.skin.plugin_manager.settings_widget.qt_compat import QWidget, QLineEdit
from itview.skin.plugin_manager.settings_widget.views.editors.base_editor import BaseEditor
from itview.skin.plugin_manager.settings_widget.models.setting_item import SettingItem


class StringEditor(BaseEditor):
    """
    Editor for string settings using a text input.

    Displays a single-line text input field.
    """

    def __init__(
        self,
        setting: SettingItem,
        parent: Optional[QWidget] = None
    ):
        """
        Initializes the string editor.

        Args:
            setting: The string setting to edit
            parent: Optional parent widget
        """
        super().__init__(setting, parent)

    def _setup_editor(self) -> None:
        """Creates the text input control."""
        self._line_edit = QLineEdit()
        self._line_edit.setPlaceholderText(self._setting.placeholder)
        self._line_edit.setStyleSheet("""
            QLineEdit {
                background: #3c3c3c;
                border: 1px solid #5a5a5a;
                border-radius: 3px;
                padding: 6px 10px;
                color: #cccccc;
                font-size: 13px;
            }
        """)
        self._line_edit.setMinimumWidth(300)
        self._line_edit.setMaximumWidth(500)
        self._line_edit.textChanged.connect(self._on_text_changed)
        self._editor_layout.addWidget(self._line_edit)
        self._editor_layout.addStretch()

    def _load_value(self) -> None:
        """Loads the current value into the text input."""
        self._line_edit.blockSignals(True)
        value = self._setting.get_value()
        self._line_edit.setText(str(value) if value is not None else "")
        self._line_edit.blockSignals(False)

    def get_value(self) -> str:
        """Returns the current text value."""
        return self._line_edit.text()

    def _on_text_changed(self, text: str) -> None:
        """Handles text changes."""
        self._on_value_changed()
