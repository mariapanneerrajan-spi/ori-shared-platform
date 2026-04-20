"""
EnumEditor - Dropdown editor for enum/choice settings.
"""

from typing import Any, Dict, List, Optional, Union

from rpa.app.skin.plugin_manager.settings_widget.qt_compat import QWidget, QComboBox
from rpa.app.skin.plugin_manager.settings_widget.views.editors.base_editor import BaseEditor
from rpa.app.skin.plugin_manager.settings_widget.models.setting_item import SettingItem
from rpa.app.skin.widgets.dropdown_combobox import DropdownComboBox


class EnumEditor(BaseEditor):
    """
    Editor for enum settings using a dropdown/combobox.

    Displays a dropdown with predefined options.
    Options can be simple strings or dicts with 'value' and 'label' keys.
    """

    def __init__(
        self,
        setting: SettingItem,
        parent: Optional[QWidget] = None
    ):
        """
        Initializes the enum editor.

        Args:
            setting: The enum setting to edit
            parent: Optional parent widget
        """
        super().__init__(setting, parent)

    def _setup_editor(self) -> None:
        """Creates the combobox control."""
        self._combobox = DropdownComboBox()
        self._combobox.setStyleSheet("""
            QComboBox {
                font-size: 14px;
                background: #3c3c3c;
                padding: 5px;
            }
        """)

        # Populate options
        self._option_values: List[str] = []
        for option in self._setting.options:
            if isinstance(option, dict):
                label = option.get("label", option.get("value", ""))
                value = option.get("value", label)
            else:
                label = str(option)
                value = option

            self._combobox.addItem(label)
            self._option_values.append(value)

        self._combobox.currentIndexChanged.connect(self._on_index_changed)
        self._editor_layout.addWidget(self._combobox)
        self._editor_layout.addStretch()

    def _load_value(self) -> None:
        """Loads the current value into the combobox."""
        self._combobox.blockSignals(True)
        value = self._setting.get_value()

        # Find matching index
        try:
            index = self._option_values.index(value)
            self._combobox.setCurrentIndex(index)
        except ValueError:
            # Value not in options, try first item
            if self._option_values:
                self._combobox.setCurrentIndex(0)

        self._combobox.blockSignals(False)

    def get_value(self) -> Any:
        """Returns the currently selected option value."""
        index = self._combobox.currentIndex()
        if 0 <= index < len(self._option_values):
            return self._option_values[index]
        return None

    def _on_index_changed(self, index: int) -> None:
        """Handles combobox selection changes."""
        self._on_value_changed()
