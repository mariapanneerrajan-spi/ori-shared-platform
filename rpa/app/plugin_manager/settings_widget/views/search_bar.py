"""
SearchBar - Search input component for filtering settings.

Provides real-time search with debouncing to avoid excessive updates.
"""

from typing import Optional

from rpa.app.plugin_manager.settings_widget.qt_compat import (
    QWidget,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QLabel,
    Signal,
    QTimer,
)


class SearchBar(QWidget):
    """
    Search input widget for filtering settings.

    Features:
    - Real-time search with configurable debounce
    - Clear button for quick reset
    - Result count display

    Signals:
        search_changed: Emitted when search query changes (after debounce)
    """

    search_changed = Signal(str)  # Emits the search query

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        debounce_ms: int = 300
    ):
        """
        Initializes the search bar.

        Args:
            parent: Optional parent widget
            debounce_ms: Milliseconds to wait before emitting search_changed
        """
        super().__init__(parent)
        self._debounce_ms = debounce_ms
        self._setup_ui()
        self._setup_debounce()

    def _setup_ui(self) -> None:
        """Creates the search bar UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(8)

        # Search input
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("Search settings...")
        self._search_input.setStyleSheet("""
            QLineEdit {
                background: #3c3c3c;
                border: 1px solid #5a5a5a;
                border-radius: 3px;
                padding: 3px 8px;
                color: #cccccc;
                height: 40px;
                font-size: 14px;
            }
            QLineEdit:hover {
                border-color: #6a6a6a;
            }
        """)
        self._search_input.textChanged.connect(self._on_text_changed)
        layout.addWidget(self._search_input)

        # Clear button
        self._clear_button = QPushButton("×")
        self._clear_button.setFixedSize(28, 28)
        self._clear_button.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #888888;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                color: #cccccc;
            }
        """)
        self._clear_button.clicked.connect(self.clear)
        self._clear_button.setVisible(False)
        layout.addWidget(self._clear_button)

        # Result count label
        self._result_label = QLabel()
        self._result_label.setStyleSheet("color: #888888; font-size: 12px;")
        self._result_label.setVisible(False)
        layout.addWidget(self._result_label)

    def _setup_debounce(self) -> None:
        """Sets up debounce timer for search."""
        self._debounce_timer = QTimer(self)
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.timeout.connect(self._emit_search)

    def _on_text_changed(self, text: str) -> None:
        """Handles text input changes with debouncing."""
        self._clear_button.setVisible(bool(text))
        self._debounce_timer.stop()
        self._debounce_timer.start(self._debounce_ms)

    def _emit_search(self) -> None:
        """Emits the search_changed signal."""
        self.search_changed.emit(self._search_input.text())

    def clear(self) -> None:
        """Clears the search input."""
        self._search_input.clear()
        self._result_label.setVisible(False)

    def get_query(self) -> str:
        """Returns the current search query."""
        return self._search_input.text()

    def set_result_count(self, count: int, total: int) -> None:
        """
        Updates the result count display.

        Args:
            count: Number of matching results
            total: Total number of settings
        """
        if self._search_input.text():
            self._result_label.setText(f"{count} of {total} settings")
            self._result_label.setVisible(True)
        else:
            self._result_label.setVisible(False)

    def set_placeholder(self, text: str) -> None:
        """Sets the placeholder text."""
        self._search_input.setPlaceholderText(text)

    def focus(self) -> None:
        """Sets focus to the search input."""
        self._search_input.setFocus()
