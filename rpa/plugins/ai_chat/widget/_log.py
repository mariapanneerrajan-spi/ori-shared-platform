"""
File logger for the AI Chat plugin.

Writes to ``~/.rpa_app/ai_chat.log`` and also enables Python's faulthandler
against the same file so C-level crashes (segfaults inside Qt, etc.) leave a
trail. Every log line is flushed immediately, so a hard crash mid-init still
yields a useful tail.

Kept dependency-free (stdlib only) and importable on its own so the rest of
the plugin can fail without breaking the logger.
"""
import datetime
import faulthandler
import os
import sys
import threading
import traceback


_LOCK = threading.Lock()
_LOG_FILE = None
_LOG_PATH = None
_FAULT_FILE = None


def _resolve_log_path() -> str:
    base = os.path.join(os.path.expanduser("~"), ".rpa_app")
    try:
        os.makedirs(base, exist_ok=True)
    except Exception:
        # Fall back to temp if the user dir is not writable.
        import tempfile
        base = tempfile.gettempdir()
    return os.path.join(base, "ai_chat.log")


def _ensure_open():
    global _LOG_FILE, _LOG_PATH, _FAULT_FILE
    if _LOG_FILE is not None:
        return
    _LOG_PATH = _resolve_log_path()
    # 'a' so successive launches append; rotate manually if it grows.
    _LOG_FILE = open(_LOG_PATH, "a", encoding="utf-8", buffering=1)
    # Separate handle for faulthandler (it needs a real fd).
    try:
        _FAULT_FILE = open(_LOG_PATH + ".fault", "a", encoding="utf-8",
                           buffering=1)
        faulthandler.enable(file=_FAULT_FILE, all_threads=True)
    except Exception:
        # faulthandler is best-effort; never let it block normal logging.
        _FAULT_FILE = None


def log_path() -> str:
    _ensure_open()
    return _LOG_PATH or "<unset>"


def log(msg: str) -> None:
    try:
        _ensure_open()
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        with _LOCK:
            _LOG_FILE.write(f"[{ts}] [pid={os.getpid()}] {msg}\n")
            _LOG_FILE.flush()
    except Exception:
        # Logging must never raise.
        pass


def log_exc(prefix: str = "") -> None:
    try:
        tb = traceback.format_exc()
    except Exception:
        tb = "<traceback unavailable>"
    log(f"{prefix}\n{tb}".rstrip())


def log_banner(title: str) -> None:
    log("=" * 60)
    log(title)
    log(f"python={sys.version.splitlines()[0]}")
    log(f"executable={sys.executable}")
    log(f"cwd={os.getcwd()}")
    log("=" * 60)
