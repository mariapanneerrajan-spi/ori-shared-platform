"""
BooleanEditor - Checkbox editor for boolean settings.
"""

from typing import Any, Optional

from rpa.app.plugin_manager.settings_widget.qt_compat import QWidget, QCheckBox
from rpa.app.plugin_manager.settings_widget.views.editors.base_editor import BaseEditor
from rpa.app.plugin_manager.settings_widget.models.setting_item import SettingItem


class BooleanEditor(BaseEditor):
    """
    Editor for boolean settings using a checkbox.

    Displays a checkbox that the user can toggle on/off.
    """

    def __init__(
        self,
        setting: SettingItem,
        parent: Optional[QWidget] = None
    ):
        """
        Initializes the boolean editor.

        Args:
            setting: The boolean setting to edit
            parent: Optional parent widget
        """
        super().__init__(setting, parent)

    def _setup_editor(self) -> None:
        """Creates the checkbox control."""
        self._checkbox = QCheckBox()
        self._checkbox.setStyleSheet("""
            QCheckBox {
                color: #cccccc;
                background: #3c3c3c;
                spacing: 0px;
                border-radius: 2px;
                border: 1px solid #5a5a5a;
            }
            QCheckBox::indicator {
                width: 21px;
                height: 21px;
            }
        """)
        self._checkbox.stateChanged.connect(self._on_checkbox_changed)
        self._editor_layout.addWidget(self._checkbox)
        self._editor_layout.addStretch()

    def _load_value(self) -> None:
        """Loads the current value into the checkbox."""
        # Block signals to prevent triggering change during load
        self._checkbox.blockSignals(True)
        self._checkbox.setChecked(bool(self._setting.get_value()))
        self._checkbox.blockSignals(False)

    def get_value(self) -> bool:
        """Returns the current checkbox state."""
        return self._checkbox.isChecked()

    def _on_checkbox_changed(self, state: int) -> None:
        """Handles checkbox state changes."""
        self._on_value_changed()
