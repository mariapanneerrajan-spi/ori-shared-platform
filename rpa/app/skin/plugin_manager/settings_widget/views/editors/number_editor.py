"""
NumberEditor - Spinbox editors for numeric settings.

Contains IntegerEditor and NumberEditor for int and float types.
"""

from typing import Any, Optional, Union

from rpa.app.skin.plugin_manager.settings_widget.qt_compat import QWidget, QSpinBox, QDoubleSpinBox
from rpa.app.skin.plugin_manager.settings_widget.views.editors.base_editor import BaseEditor
from rpa.app.skin.plugin_manager.settings_widget.models.setting_item import SettingItem


class IntegerEditor(BaseEditor):
    """
    Editor for integer settings using a spinbox.

    Displays a spinbox with increment/decrement buttons.
    """

    def __init__(
        self,
        setting: SettingItem,
        parent: Optional[QWidget] = None
    ):
        """
        Initializes the integer editor.

        Args:
            setting: The integer setting to edit
            parent: Optional parent widget
        """
        super().__init__(setting, parent)

    def _setup_editor(self) -> None:
        """Creates the spinbox control."""
        self._spinbox = QSpinBox()

        # Set range
        minimum = self._setting.minimum if self._setting.minimum is not None else -999999
        maximum = self._setting.maximum if self._setting.maximum is not None else 999999
        self._spinbox.setRange(int(minimum), int(maximum))
        self._spinbox.setSingleStep(int(self._setting.step))

        self._spinbox.setStyleSheet("""
            QSpinBox {
                font-size: 14px;
                background: #3c3c3c;
                padding-right: 10px;
                min-height: 24px;
            }
        """)

        self._spinbox.valueChanged.connect(self._on_spinbox_changed)
        self._editor_layout.addWidget(self._spinbox)
        self._editor_layout.addStretch()

    def _load_value(self) -> None:
        """Loads the current value into the spinbox."""
        self._spinbox.blockSignals(True)
        value = self._setting.get_value()
        self._spinbox.setValue(int(value) if value is not None else 0)
        self._spinbox.blockSignals(False)

    def get_value(self) -> int:
        """Returns the current spinbox value."""
        return self._spinbox.value()

    def _on_spinbox_changed(self, value: int) -> None:
        """Handles spinbox value changes."""
        self._on_value_changed()


class NumberEditor(BaseEditor):
    """
    Editor for decimal number settings using a double spinbox.

    Displays a spinbox that accepts floating-point values.
    """

    def __init__(
        self,
        setting: SettingItem,
        parent: Optional[QWidget] = None
    ):
        """
        Initializes the number editor.

        Args:
            setting: The number setting to edit
            parent: Optional parent widget
        """
        super().__init__(setting, parent)

    def _setup_editor(self) -> None:
        """Creates the double spinbox control."""
        self._spinbox = QDoubleSpinBox()

        # Set range
        minimum = self._setting.minimum if self._setting.minimum is not None else -999999.0
        maximum = self._setting.maximum if self._setting.maximum is not None else 999999.0
        self._spinbox.setRange(float(minimum), float(maximum))
        self._spinbox.setSingleStep(float(self._setting.step))
        self._spinbox.setDecimals(2)

        self._spinbox.setStyleSheet("""
            QDoubleSpinBox {
                font-size: 14px;
                background: #3c3c3c;
                padding-right: 10px;
                min-height: 24px;    
            }
        """)

        self._spinbox.valueChanged.connect(self._on_spinbox_changed)
        self._editor_layout.addWidget(self._spinbox)
        self._editor_layout.addStretch()

    def _load_value(self) -> None:
        """Loads the current value into the spinbox."""
        self._spinbox.blockSignals(True)
        value = self._setting.get_value()
        self._spinbox.setValue(float(value) if value is not None else 0.0)
        self._spinbox.blockSignals(False)

    def get_value(self) -> float:
        """Returns the current spinbox value."""
        return self._spinbox.value()

    def _on_spinbox_changed(self, value: float) -> None:
        """Handles spinbox value changes."""
        self._on_value_changed()
