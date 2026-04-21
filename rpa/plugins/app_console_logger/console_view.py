"""Console Logger dock widget UI.

Displays a stream of log entries (prints + RPA log records) in a read-only
monospace text area. Provides a toolbar with per-category/per-level filter
toggles, a substring search, and a clear button. Entries are retained in a
bounded ring buffer so filters can be toggled without losing history.
"""
import html
import time
from collections import deque

from rpa.utils.qt import QtCore, QtGui, QtWidgets


# Categories used for filtering — match the (category, level) values
# emitted by LogBridge in log_bridge.py.
_PRINT_STDOUT = ("print", "STDOUT")
_PRINT_STDERR = ("print", "STDERR")
_RPA_DEBUG = ("rpa", "DEBUG")
_RPA_INFO = ("rpa", "INFO")
_RPA_WARNING = ("rpa", "WARNING")
_RPA_ERROR = ("rpa", "ERROR")
_RPA_CRITICAL = ("rpa", "CRITICAL")

# Display colors (hex) for each (category, level) bucket.
_COLORS = {
    _PRINT_STDOUT: "#cccccc",
    _PRINT_STDERR: "#ff8c5a",
    _RPA_DEBUG: "#888888",
    _RPA_INFO: "#5ac8fa",
    _RPA_WARNING: "#f5c542",
    _RPA_ERROR: "#ff5a5a",
    _RPA_CRITICAL: "#ff5af5",
}

# Human-readable tag shown inline in each entry.
_TAG = {
    _PRINT_STDOUT: "[PRINT stdout]",
    _PRINT_STDERR: "[PRINT stderr]",
    _RPA_DEBUG: "[RPA DEBUG]",
    _RPA_INFO: "[RPA INFO]",
    _RPA_WARNING: "[RPA WARNING]",
    _RPA_ERROR: "[RPA ERROR]",
    _RPA_CRITICAL: "[RPA CRITICAL]",
}

# Toolbar toggle button labels -> bucket key.
_FILTER_BUTTONS = [
    ("Print stdout", _PRINT_STDOUT),
    ("Print stderr", _PRINT_STDERR),
    ("RPA DEBUG", _RPA_DEBUG),
    ("RPA INFO", _RPA_INFO),
    ("RPA WARNING", _RPA_WARNING),
    ("RPA ERROR", _RPA_ERROR),
    ("RPA CRITICAL", _RPA_CRITICAL),
]

_MAX_ENTRIES = 5000


class ConsoleView(QtWidgets.QWidget):
    """Dock widget content: toolbar + filter toggles + read-only text area."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._entries = deque(maxlen=_MAX_ENTRIES)
        self._active = {key: True for _, key in _FILTER_BUTTONS}
        self._search_text = ""

        self._build_ui()

    # ---------- UI construction ----------

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        toolbar = QtWidgets.QToolBar(self)
        toolbar.setToolButtonStyle(QtCore.Qt.ToolButtonTextOnly)
        toolbar.setIconSize(QtCore.QSize(16, 16))

        self._filter_buttons = {}
        for label, key in _FILTER_BUTTONS:
            btn = QtWidgets.QToolButton(toolbar)
            btn.setText(label)
            btn.setCheckable(True)
            btn.setChecked(True)
            color = _COLORS[key]
            btn.setStyleSheet(
                "QToolButton { padding: 2px 6px; margin: 2px; }"
                "QToolButton:checked { "
                f"  background-color: {color}; color: #111; "
                "  border: 1px solid #222; border-radius: 3px; }"
                "QToolButton:!checked { "
                "  background-color: transparent; "
                f"  color: {color}; "
                f"  border: 1px solid {color}; border-radius: 3px; }}"
            )
            btn.toggled.connect(self._on_filter_toggled)
            # Stash key on the button so the slot can find it.
            btn.setProperty("_bucket_key", "{}|{}".format(*key))
            toolbar.addWidget(btn)
            self._filter_buttons[key] = btn

        toolbar.addSeparator()

        self._search_edit = QtWidgets.QLineEdit(toolbar)
        self._search_edit.setPlaceholderText("Search...")
        self._search_edit.setClearButtonEnabled(True)
        self._search_edit.setMaximumWidth(240)
        self._search_edit.textChanged.connect(self._on_search_changed)
        toolbar.addWidget(self._search_edit)

        toolbar.addSeparator()

        clear_btn = QtWidgets.QToolButton(toolbar)
        clear_btn.setText("Clear")
        clear_btn.clicked.connect(self._on_clear)
        toolbar.addWidget(clear_btn)

        layout.addWidget(toolbar)

        self._text = QtWidgets.QPlainTextEdit(self)
        self._text.setReadOnly(True)
        self._text.setLineWrapMode(QtWidgets.QPlainTextEdit.NoWrap)
        self._text.setMaximumBlockCount(_MAX_ENTRIES)
        font = QtGui.QFont("Consolas")
        font.setStyleHint(QtGui.QFont.Monospace)
        font.setPointSize(9)
        self._text.setFont(font)
        # Dark background improves color contrast for the level colors.
        self._text.setStyleSheet(
            "QPlainTextEdit { background-color: #1e1e1e; color: #dddddd; }"
        )
        layout.addWidget(self._text, 1)

    # ---------- Public slot ----------

    @QtCore.Slot(str, str, str, str)
    def append_entry(self, category, level, logger_name, message):
        """Slot connected to LogBridge.SIG_ENTRY (QueuedConnection)."""
        ts = time.strftime("%H:%M:%S")
        entry = (ts, category, level, logger_name, message)
        self._entries.append(entry)
        if self._passes_filters(entry):
            self._text.appendHtml(self._format_entry_html(entry))

    # ---------- Filtering ----------

    def _on_filter_toggled(self, checked):
        btn = self.sender()
        if btn is None:
            return
        raw = btn.property("_bucket_key")
        if not raw:
            return
        cat, lvl = raw.split("|", 1)
        self._active[(cat, lvl)] = bool(checked)
        self._refresh()

    def _on_search_changed(self, text):
        self._search_text = text or ""
        self._refresh()

    def _on_clear(self):
        self._entries.clear()
        self._text.clear()

    def _passes_filters(self, entry):
        _, category, level, _logger, message = entry
        key = (category, level)
        if key not in self._active:
            # Unknown bucket — default to show so nothing is silently dropped.
            pass
        elif not self._active[key]:
            return False
        if self._search_text:
            if self._search_text.lower() not in message.lower():
                return False
        return True

    def _refresh(self):
        """Re-render the text area from the retained entries."""
        self._text.clear()
        lines = []
        for entry in self._entries:
            if self._passes_filters(entry):
                lines.append(self._format_entry_html(entry))
        if lines:
            self._text.appendHtml("<br>".join(lines))

    # ---------- Formatting ----------

    @staticmethod
    def _format_entry_html(entry):
        ts, category, level, logger_name, message = entry
        key = (category, level)
        color = _COLORS.get(key, "#dddddd")
        tag = _TAG.get(key, f"[{category.upper()} {level}]")
        safe_msg = html.escape(message).replace("\n", "<br>")
        if category == "rpa" and logger_name:
            safe_logger = html.escape(logger_name)
            body = (
                f"<span style='color:{color};'>"
                f"[{ts}] {tag} {safe_logger}: {safe_msg}"
                f"</span>"
            )
        else:
            body = (
                f"<span style='color:{color};'>"
                f"[{ts}] {tag} {safe_msg}"
                f"</span>"
            )
        return body
