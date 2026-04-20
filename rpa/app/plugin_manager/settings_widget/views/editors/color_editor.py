"""
ColorEditor - Color picker editor for color settings.
"""

from typing import Any, Optional

from rpa.app.plugin_manager.settings_widget.qt_compat import (
    QWidget,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QColorDialog,
    QColor,
)
from rpa.app.plugin_manager.settings_widget.views.editors.base_editor import BaseEditor
from rpa.app.plugin_manager.settings_widget.models.setting_item import SettingItem


class ColorEditor(BaseEditor):
    """
    Editor for color settings.

    Displays a color preview button that opens a color dialog,
    and a text input for direct hex color entry.
    """

    def __init__(
        self,
        setting: SettingItem,
        parent: Optional[QWidget] = None
    ):
        """
        Initializes the color editor.

        Args:
            setting: The color setting to edit
            parent: Optional parent widget
        """
        super().__init__(setting, parent)

    def _setup_editor(self) -> None:
        """Creates the color preview button and hex input."""
        # Color preview button
        self._color_button = QPushButton()
        self._color_button.setFixedSize(32, 32)
        self._color_button.clicked.connect(self._open_color_dialog)
        self._editor_layout.addWidget(self._color_button)

        # Hex color input
        self._hex_input = QLineEdit()
        self._hex_input.setPlaceholderText("#RRGGBB")
        self._hex_input.setMaximumWidth(100)
        self._hex_input.setStyleSheet("""
            QLineEdit {
                background: #3c3c3c;
                border: 1px solid #5a5a5a;
                border-radius: 3px;
                padding: 6px 10px;
                color: #cccccc;
                font-size: 13px;
            }
        """)
        self._hex_input.textChanged.connect(self._on_hex_changed)
        self._editor_layout.addWidget(self._hex_input)
        self._editor_layout.addStretch()

    def _load_value(self) -> None:
        """Loads the current value into the controls."""
        self._hex_input.blockSignals(True)

        value = self._setting.get_value()
        color_str = str(value) if value else "#000000"

        # Ensure it starts with #
        if not color_str.startswith("#"):
            color_str = f"#{color_str}"

        self._hex_input.setText(color_str)
        self._update_color_button(color_str)

        self._hex_input.blockSignals(False)

    def get_value(self) -> str:
        """Returns the current color as a hex string."""
        return self._hex_input.text()

    def _on_hex_changed(self, text: str) -> None:
        """Handles hex input changes."""
        self._update_color_button(text)
        self._on_value_changed()

    def _update_color_button(self, color_str: str) -> None:
        """Updates the color button preview."""
        # Validate and set color
        if QColor(color_str).isValid():
            self._color_button.setStyleSheet(f"""
                QPushButton {{
                    background: {color_str};
                    border: 1px solid #5a5a5a;
                    border-radius: 4px;
                }}
                QPushButton:hover {{
                    border-color: #8a8a8a;
                }}
            """)
        else:
            self._color_button.setStyleSheet("""
                QPushButton {
                    background: #3c3c3c;
                    border: 1px solid #ff0000;
                    border-radius: 4px;
                }
            """)

    def _open_color_dialog(self) -> None:
        """Opens the color picker dialog."""
        current_color = QColor(self._hex_input.text())
        if not current_color.isValid():
            current_color = QColor("#000000")

        color = QColorDialog.getColor(
            current_color,
            self,
            "Select Color"
        )

        if color.isValid():
            self._hex_input.setText(color.name())
