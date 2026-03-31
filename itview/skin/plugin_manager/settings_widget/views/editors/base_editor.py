"""
BaseEditor - Abstract base class for all setting editor widgets.

Defines the interface that all editor types must implement,
ensuring consistent behavior across different setting types.
"""

from abc import abstractmethod
from typing import Any, Optional

from itview.skin.plugin_manager.settings_widget.qt_compat import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    Signal,
    QFont,
    QSizePolicy,
)
from itview.skin.plugin_manager.settings_widget.models.setting_item import SettingItem


class BaseEditor(QWidget):
    """
    Abstract base class for setting editor widgets.

    Each editor displays a setting's title, description, and provides
    an appropriate input control for modifying the value.

    Signals:
        value_changed: Emitted when the user changes the setting value
    """

    value_changed = Signal(object)  # Emits the new value

    def __init__(
        self,
        setting: SettingItem,
        parent: Optional[QWidget] = None
    ):
        """
        Initializes the base editor.

        Args:
            setting: The setting item this editor controls
            parent: Optional parent widget
        """
        super().__init__(parent)
        self._setting = setting
        self._setup_base_ui()
        self._setup_editor()
        self._load_value()

    @property
    def setting(self) -> SettingItem:
        """Returns the setting item this editor controls."""
        return self._setting

    def _setup_base_ui(self) -> None:
        """Sets up the common UI structure for all editors."""
        self._main_layout = QVBoxLayout(self)
        self._main_layout.setContentsMargins(0, 10, 0, 10)
        self._main_layout.setSpacing(4)

        # Header row with title and reset button
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)

        # Title label
        self._title_label = QLabel(self._setting.title)
        title_font = QFont()
        title_font.setBold(True)
        self._title_label.setFont(title_font)
        self._title_label.setStyleSheet("color: #cccccc; font-size: 15px; font-weight: 600;")
        header_layout.addWidget(self._title_label)

        # Setting ID label (subtle)
        # self._id_label = QLabel(f"({self._setting.full_id})")
        # self._id_label.setStyleSheet("color: #666666; font-size: 11px;")
        # header_layout.addWidget(self._id_label)

        header_layout.addStretch()

        # Reset button (only shown when modified)
        self._reset_button = QPushButton("Reset")
        self._reset_button.setFixedWidth(50)
        self._reset_button.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #569cd6;
                border: none;
                font-size: 11px;
            }
            QPushButton:hover {
                text-decoration: underline;
            }
        """)
        self._reset_button.clicked.connect(self._on_reset)
        self._reset_button.setVisible(self._setting.is_modified())
        header_layout.addWidget(self._reset_button)

        self._main_layout.addLayout(header_layout)

        # Description label
        if self._setting.description:
            self._description_label = QLabel(self._setting.description)
            self._description_label.setWordWrap(True)
            self._description_label.setStyleSheet("color: #969696; font-size: 13px;")
            self._main_layout.addWidget(self._description_label)

        # Container for the actual editor control
        self._editor_container = QWidget()
        self._editor_layout = QHBoxLayout(self._editor_container)
        self._editor_layout.setContentsMargins(0, 4, 0, 0)
        self._main_layout.addWidget(self._editor_container)

        # Set size policy
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    @abstractmethod
    def _setup_editor(self) -> None:
        """
        Sets up the specific editor control.

        Subclasses must implement this to add their input widget(s)
        to self._editor_layout.
        """
        pass

    @abstractmethod
    def _load_value(self) -> None:
        """
        Loads the current setting value into the editor control.

        Subclasses must implement this to populate their input widget(s)
        with the current value from self._setting.
        """
        pass

    @abstractmethod
    def get_value(self) -> Any:
        """
        Returns the current value from the editor control.

        Returns:
            The current value in the appropriate type
        """
        pass

    def set_value(self, value: Any) -> None:
        """
        Sets the editor control to display the given value.

        Args:
            value: The value to display
        """
        self._setting.set_value(value)
        self._load_value()
        self._update_modified_state()

    def _on_value_changed(self) -> None:
        """Called when the user changes the value in the editor control."""
        value = self.get_value()
        if self._setting.validate(value):
            self._setting.set_value(value)
            self._update_modified_state()
            self.value_changed.emit(value)

    def _on_reset(self) -> None:
        """Resets the setting to its default value."""
        self._setting.reset_to_default()
        self._load_value()
        self._update_modified_state()
        self.value_changed.emit(self._setting.get_value())

    def _update_modified_state(self) -> None:
        """Updates UI to reflect whether the setting is modified."""
        is_modified = self._setting.is_modified()
        self._reset_button.setVisible(is_modified)

        # Visual indicator for modified settings
        if is_modified:
            self._title_label.setStyleSheet("color: #dcdcaa; font-weight: 600;")  # Yellow tint
        else:
            self._title_label.setStyleSheet("color: #cccccc;")

    def matches_search(self, query: str) -> bool:
        """
        Checks if this editor matches a search query.

        Args:
            query: Search query string

        Returns:
            True if the setting matches the query
        """
        query_lower = query.lower()
        return (
            query_lower in self._setting.title.lower() or
            query_lower in self._setting.description.lower() or
            query_lower in self._setting.id.lower() or
            query_lower in self._setting.full_id.lower() or
            any(query_lower in tag.lower() for tag in self._setting.tags)
        )
