"""
PathEditor - File and directory path editors.

Contains FilePathEditor and DirPathEditor for path selection.
"""

from typing import Any, Optional

from rpa.app.plugin_manager.settings_widget.qt_compat import (
    QWidget,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QFileDialog,
)
from rpa.app.plugin_manager.settings_widget.views.editors.base_editor import BaseEditor
from rpa.app.plugin_manager.settings_widget.models.setting_item import SettingItem


class FilePathEditor(BaseEditor):
    """
    Editor for file path settings.

    Displays a text input with a browse button that opens a file dialog.
    """

    def __init__(
        self,
        setting: SettingItem,
        parent: Optional[QWidget] = None
    ):
        """
        Initializes the file path editor.

        Args:
            setting: The file path setting to edit
            parent: Optional parent widget
        """
        super().__init__(setting, parent)

    def _setup_editor(self) -> None:
        """Creates the path input with browse button."""
        self._line_edit = QLineEdit()
        self._line_edit.setPlaceholderText("Select a file...")
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
        self._line_edit.textChanged.connect(self._on_text_changed)
        self._editor_layout.addWidget(self._line_edit)

        self._browse_button = QPushButton("Browse...")
        self._browse_button.setStyleSheet("""
            QPushButton {
                background: #4a4a4a;
                border: 1px solid #5a5a5a;
                border-radius: 3px;
                padding: 6px 16px;
                color: #cccccc;
                font-size: 13px;
            }
            QPushButton:hover {
                background: #5a5a5a;
            }
        """)
        self._browse_button.clicked.connect(self._browse_file)
        self._editor_layout.addWidget(self._browse_button)
        self._editor_layout.addStretch()

    def _load_value(self) -> None:
        """Loads the current value into the text input."""
        self._line_edit.blockSignals(True)
        value = self._setting.get_value()
        self._line_edit.setText(str(value) if value else "")
        self._line_edit.blockSignals(False)

    def get_value(self) -> str:
        """Returns the current path value."""
        return self._line_edit.text()

    def _on_text_changed(self, text: str) -> None:
        """Handles text changes."""
        self._on_value_changed()

    def _browse_file(self) -> None:
        """Opens a file dialog for path selection."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select File",
            self._line_edit.text(),
            self._setting.file_filter
        )
        if file_path:
            self._line_edit.setText(file_path)


class DirPathEditor(BaseEditor):
    """
    Editor for directory path settings.

    Displays a text input with a browse button that opens a directory dialog.
    """

    def __init__(
        self,
        setting: SettingItem,
        parent: Optional[QWidget] = None
    ):
        """
        Initializes the directory path editor.

        Args:
            setting: The directory path setting to edit
            parent: Optional parent widget
        """
        super().__init__(setting, parent)

    def _setup_editor(self) -> None:
        """Creates the path input with browse button."""
        self._line_edit = QLineEdit()
        self._line_edit.setPlaceholderText("Select a directory...")
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
        self._line_edit.textChanged.connect(self._on_text_changed)
        self._editor_layout.addWidget(self._line_edit)

        self._browse_button = QPushButton("Browse...")
        self._browse_button.setStyleSheet("""
            QPushButton {
                background: #4a4a4a;
                border: 1px solid #5a5a5a;
                border-radius: 3px;
                padding: 6px 16px;
                color: #cccccc;
                font-size: 13px;
            }
            QPushButton:hover {
                background: #5a5a5a;
            }
        """)
        self._browse_button.clicked.connect(self._browse_directory)
        self._editor_layout.addWidget(self._browse_button)
        self._editor_layout.addStretch()

    def _load_value(self) -> None:
        """Loads the current value into the text input."""
        self._line_edit.blockSignals(True)
        value = self._setting.get_value()
        self._line_edit.setText(str(value) if value else "")
        self._line_edit.blockSignals(False)

    def get_value(self) -> str:
        """Returns the current path value."""
        return self._line_edit.text()

    def _on_text_changed(self, text: str) -> None:
        """Handles text changes."""
        self._on_value_changed()

    def _browse_directory(self) -> None:
        """Opens a directory dialog for path selection."""
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "Select Directory",
            self._line_edit.text()
        )
        if dir_path:
            self._line_edit.setText(dir_path)
