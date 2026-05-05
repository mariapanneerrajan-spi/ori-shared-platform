"""
Chat panel widget for the AI Chat plugin.

Layout: scrollable transcript on top, input box at the bottom, action buttons
in between. Settings (API key, model, max iterations) are persisted via
``QSettings("imageworks.com", "rpa_app")`` under the ``ai_chat/`` group.
"""
import json
import os

from rpa.utils.qt import QtCore, QtGui, QtWidgets

from ._log import log, log_exc
from .chat_client import (
    ChatClient,
    DEFAULT_MAX_TOOL_ITERATIONS,
    DEFAULT_MODEL,
)


_SETTINGS_GROUP = "ai_chat"

# Curated list of Claude models the UI offers. (label, model_id) pairs.
# Default first; ordered roughly fastest -> most capable so the dropdown is
# easy to scan. Users can still override by typing a custom id below.
_MODEL_OPTIONS = [
    ("Haiku 4.5  (fastest, recommended)", "claude-haiku-4-5-20251001"),
    ("Sonnet 4.6  (balanced)",            "claude-sonnet-4-6"),
    ("Opus 4.7  (most capable)",          "claude-opus-4-7"),
]


def _load_settings():
    s = QtCore.QSettings("imageworks.com", "rpa_app")
    s.beginGroup(_SETTINGS_GROUP)
    api_key = s.value("api_key", "", type=str) or ""
    model = s.value("model", DEFAULT_MODEL, type=str) or DEFAULT_MODEL
    max_iters = int(s.value("max_iters", DEFAULT_MAX_TOOL_ITERATIONS) or
                    DEFAULT_MAX_TOOL_ITERATIONS)
    s.endGroup()
    return api_key, model, max_iters


def _save_settings(api_key, model, max_iters):
    s = QtCore.QSettings("imageworks.com", "rpa_app")
    s.beginGroup(_SETTINGS_GROUP)
    s.setValue("api_key", api_key)
    s.setValue("model", model)
    s.setValue("max_iters", int(max_iters))
    s.endGroup()


class _SettingsDialog(QtWidgets.QDialog):
    def __init__(self, api_key, model, max_iters, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AI Chat Settings")
        self.setModal(True)

        form = QtWidgets.QFormLayout(self)
        self._api_key_edit = QtWidgets.QLineEdit(api_key)
        self._api_key_edit.setEchoMode(QtWidgets.QLineEdit.Password)
        self._api_key_edit.setPlaceholderText("sk-ant-...")
        form.addRow("Anthropic API Key:", self._api_key_edit)

        self._model_combo = QtWidgets.QComboBox()
        for label, model_id in _MODEL_OPTIONS:
            self._model_combo.addItem(label, model_id)
        # Preselect the saved model. If it's not one of the known options
        # (e.g. a custom id from QSettings), append it as an extra entry so
        # nothing gets silently changed on the user.
        idx = self._model_combo.findData(model)
        if idx < 0:
            self._model_combo.addItem(f"{model}  (custom)", model)
            idx = self._model_combo.count() - 1
        self._model_combo.setCurrentIndex(idx)
        form.addRow("Model:", self._model_combo)

        self._iters_spin = QtWidgets.QSpinBox()
        self._iters_spin.setRange(1, 200)
        self._iters_spin.setValue(int(max_iters))
        form.addRow("Max tool iterations:", self._iters_spin)

        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def values(self):
        model_id = self._model_combo.currentData() or DEFAULT_MODEL
        return (self._api_key_edit.text().strip(),
                model_id,
                int(self._iters_spin.value()))


class _Input(QtWidgets.QPlainTextEdit):
    """Plain-text input that sends on Enter, newlines on Shift+Enter."""

    SIG_SUBMIT = QtCore.Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPlaceholderText(
            "Ask the AI to drive RPA. "
            "Enter to send, Shift+Enter for newline.")
        self.setMaximumHeight(120)

    def keyPressEvent(self, event):
        if (event.key() in (QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter)
                and not event.modifiers() & QtCore.Qt.ShiftModifier):
            self.SIG_SUBMIT.emit()
            return
        super().keyPressEvent(event)


class AiChatPanel(QtWidgets.QWidget):
    def __init__(self, rpa, main_window, parent=None):
        log("AiChatPanel.__init__ start")
        super().__init__(parent if parent is not None else main_window)
        self._rpa = rpa
        self._busy = False

        try:
            api_key, model, max_iters = _load_settings()
            log(f"settings loaded: model={model} max_iters={max_iters} "
                f"api_key_present={bool(api_key)}")
        except Exception:
            log_exc("settings load failed; using defaults")
            api_key, model, max_iters = "", DEFAULT_MODEL, DEFAULT_MAX_TOOL_ITERATIONS
        # Env var wins over an empty stored key, so first-time launches with
        # ANTHROPIC_API_KEY in the environment Just Work.
        if not api_key:
            api_key = os.environ.get("ANTHROPIC_API_KEY", "") or ""
            log(f"using ANTHROPIC_API_KEY env: present={bool(api_key)}")
        self._api_key = api_key
        self._model = model
        self._max_iters = max_iters

        try:
            log("constructing ChatClient")
            self._client = ChatClient(
                rpa=rpa, api_key=api_key, model=model, max_iters=max_iters,
                parent=self)
            log(f"ChatClient ready; tool_count={self._client.tool_count()} "
                f"build_error={self._client.tool_build_error() or '<none>'}")
        except Exception:
            log_exc("FATAL: ChatClient construction failed")
            raise

        try:
            self._client.SIG_ASSISTANT_TEXT.connect(self._on_assistant_text)
            self._client.SIG_TOOL_CALL.connect(self._on_tool_call)
            self._client.SIG_TOOL_RESULT.connect(self._on_tool_result)
            self._client.SIG_DONE.connect(self._on_done)
            self._client.SIG_ERROR.connect(self._on_error)
            log("ChatClient signals connected")
        except Exception:
            log_exc("FATAL: ChatClient signal wiring failed")
            raise

        try:
            self._build_ui()
            log("UI built")
        except Exception:
            log_exc("FATAL: _build_ui failed")
            raise

        self._append_system(
            f"AI Chat ready. {self._client.tool_count()} RPA tools loaded "
            f"(model: {self._model}).")
        if not api_key:
            self._append_system(
                "No API key configured. Open settings (⚙) to add one.")
        log("AiChatPanel.__init__ DONE")

    # ---- UI -----------------------------------------------------------

    def _build_ui(self):
        self.setMinimumSize(420, 480)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)

        self._transcript = QtWidgets.QTextBrowser()
        self._transcript.setOpenExternalLinks(True)
        self._transcript.setStyleSheet(
            "QTextBrowser { background-color: #1e1e1e; color: #dcdcdc; "
            "font-family: Consolas, monospace; font-size: 13px; }")
        layout.addWidget(self._transcript, stretch=1)

        self._input = _Input()
        self._input.SIG_SUBMIT.connect(self._send)
        layout.addWidget(self._input)

        button_row = QtWidgets.QHBoxLayout()
        self._send_btn = QtWidgets.QPushButton("Send")
        self._send_btn.clicked.connect(self._send)
        self._stop_btn = QtWidgets.QPushButton("Stop")
        self._stop_btn.clicked.connect(self._client.cancel)
        self._stop_btn.setEnabled(False)
        self._clear_btn = QtWidgets.QPushButton("Clear")
        self._clear_btn.clicked.connect(self._clear)
        self._settings_btn = QtWidgets.QPushButton("⚙")
        self._settings_btn.setToolTip("Settings")
        self._settings_btn.setFixedWidth(32)
        self._settings_btn.clicked.connect(self._open_settings)
        button_row.addWidget(self._send_btn)
        button_row.addWidget(self._stop_btn)
        button_row.addWidget(self._clear_btn)
        button_row.addStretch(1)
        button_row.addWidget(self._settings_btn)
        layout.addLayout(button_row)

    # ---- Transcript helpers ------------------------------------------

    @staticmethod
    def _escape(text):
        return (text.replace("&", "&amp;")
                    .replace("<", "&lt;")
                    .replace(">", "&gt;")
                    .replace("\n", "<br>"))

    def _append(self, role, body, color):
        html = (f'<div style="margin:4px 0;">'
                f'<span style="color:{color};font-weight:bold;">{role}</span> '
                f'<span style="color:#dcdcdc;">{body}</span></div>')
        self._transcript.append(html)

    def _append_system(self, text):
        self._append("system:", self._escape(text), "#888888")

    def _append_user(self, text):
        self._append("you:", self._escape(text), "#7fb8ff")

    def _append_assistant(self, text):
        self._append("ai:", self._escape(text), "#a6e22e")

    def _append_tool_call(self, name, args):
        try:
            args_text = json.dumps(args, default=str)
        except Exception:
            args_text = repr(args)
        self._append("tool ▶", self._escape(f"{name}({args_text})"),
                     "#cccc66")

    def _append_tool_result(self, name, text, is_error):
        prefix = "tool ✖" if is_error else "tool ◀"
        color = "#ff6666" if is_error else "#888888"
        body = self._escape(f"{name} -> {text}")
        self._append(prefix, body, color)

    # ---- Actions ------------------------------------------------------

    def _send(self):
        if self._busy:
            return
        text = self._input.toPlainText().strip()
        if not text:
            return
        self._input.clear()
        self._append_user(text)
        self._set_busy(True)
        self._client.send(text)

    def _clear(self):
        self._transcript.clear()
        self._client.reset()
        self._append_system("Conversation cleared.")

    def _open_settings(self):
        dlg = _SettingsDialog(
            self._api_key, self._model, self._max_iters, parent=self)
        if dlg.exec() != QtWidgets.QDialog.Accepted:
            return
        api_key, model, max_iters = dlg.values()
        self._api_key = api_key
        self._model = model
        self._max_iters = max_iters
        _save_settings(api_key, model, max_iters)
        self._client.set_api_key(api_key)
        self._client.set_model(model)
        self._append_system(
            f"Settings updated (model: {model}, max iters: {max_iters}).")

    def set_api_key(self, api_key):
        """Public hook used by post_app_init to apply a CLI-provided key."""
        if not api_key:
            return
        self._api_key = api_key
        self._client.set_api_key(api_key)

    def set_model(self, model):
        if not model:
            return
        self._model = model
        self._client.set_model(model)

    # ---- Worker callbacks --------------------------------------------

    def _on_assistant_text(self, text):
        self._append_assistant(text)

    def _on_tool_call(self, name, args):
        self._append_tool_call(name, args or {})

    def _on_tool_result(self, name, text, is_error):
        self._append_tool_result(name, text, is_error)

    def _on_done(self):
        self._set_busy(False)

    def _on_error(self, message):
        self._append("error:", self._escape(message), "#ff6666")

    def _set_busy(self, busy):
        self._busy = busy
        self._send_btn.setEnabled(not busy)
        self._stop_btn.setEnabled(busy)
        self._input.setReadOnly(busy)

    def closeEvent(self, event):  # pragma: no cover - Qt lifecycle
        try:
            self._client.shutdown()
        finally:
            super().closeEvent(event)
