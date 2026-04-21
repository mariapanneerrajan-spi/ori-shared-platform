"""Thread-safe bridges from Python logging and sys.stdout/stderr into Qt.

All entries are marshaled through a single Qt signal (``LogBridge.SIG_ENTRY``)
which the ConsoleView connects to with ``Qt.QueuedConnection``. This ensures
GUI updates always happen on the main thread even when the originating
print() or logger call came from a non-GUI thread.
"""
import logging
from rpa.utils.qt import QtCore


class LogBridge(QtCore.QObject):
    """Owns the single Qt signal used to deliver entries to the view.

    Signal payload: (category, level_name, logger_name, message)
        category    -> "print" | "rpa"
        level_name  -> "STDOUT"/"STDERR" for prints,
                       "DEBUG"/"INFO"/"WARNING"/"ERROR"/"CRITICAL" for rpa
        logger_name -> "" for prints, full logger name for rpa records
        message     -> the formatted message text
    """
    SIG_ENTRY = QtCore.Signal(str, str, str, str)


class QtLogHandler(logging.Handler):
    """A logging.Handler that forwards records to LogBridge via its signal.

    Attached to logging.getLogger("rpa") alongside the existing
    RotatingFileHandler — this is additive, file logging is preserved.
    """
    def __init__(self, bridge: LogBridge):
        super().__init__(level=logging.DEBUG)
        self._bridge = bridge

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
            self._bridge.SIG_ENTRY.emit(
                "rpa", record.levelname, record.name, msg)
        except Exception:
            # Never let a logging failure crash the application.
            pass


class StreamTee:
    """File-like wrapper for sys.stdout / sys.stderr.

    Writes are forwarded to the original stream (so terminal output is
    preserved), then buffered until a newline is seen so one print() call
    produces one entry in the console widget.
    """
    def __init__(self, original, bridge: LogBridge, level_name: str):
        self._original = original
        self._bridge = bridge
        self._level_name = level_name  # "STDOUT" or "STDERR"
        self._buffer = ""

    def write(self, text):
        # Always pass through to the real stream first.
        try:
            n = self._original.write(text)
        except Exception:
            n = len(text) if isinstance(text, str) else 0
        try:
            self._original.flush()
        except Exception:
            pass

        if not isinstance(text, str):
            return n

        self._buffer += text
        while "\n" in self._buffer:
            line, self._buffer = self._buffer.split("\n", 1)
            if line:
                try:
                    self._bridge.SIG_ENTRY.emit(
                        "print", self._level_name, "", line)
                except Exception:
                    pass
        return n

    def flush(self):
        try:
            self._original.flush()
        except Exception:
            pass

    def isatty(self):
        try:
            return self._original.isatty()
        except Exception:
            return False

    def fileno(self):
        return self._original.fileno()

    def writable(self):
        return True

    def readable(self):
        return False

    @property
    def original(self):
        return self._original
