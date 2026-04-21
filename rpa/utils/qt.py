"""
PySide2 / PySide6 compatibility shim.

Prefers PySide6 if importable, falls back to PySide2. OpenRV exposes only the
binding it was built against, so the fallback is effectively a binding probe.

Usage (both forms work):
    from rpa.utils.qt import QtCore, QtGui, QtWidgets
    from rpa.utils.qt.QtCore import Qt, Signal

Qt5 <-> Qt6 relocations handled here so call sites can use a single spelling:
    - QAction, QActionGroup, QShortcut: available on BOTH QtGui and QtWidgets
    - QRegExp (Qt6 removed): aliased to QRegularExpression on PySide6
    - QRegExpValidator (Qt6 removed): aliased to QRegularExpressionValidator on PySide6
"""
import sys as _sys

try:
    from PySide6 import QtCore, QtGui, QtWidgets
    PYSIDE_VERSION = 6
    QT_BINDING = "PySide6"
except ImportError:
    from PySide2 import QtCore, QtGui, QtWidgets
    PYSIDE_VERSION = 2
    QT_BINDING = "PySide2"


if PYSIDE_VERSION == 2:
    # Qt6 moved these from QtWidgets to QtGui. Expose on QtGui too so Qt6-style
    # imports work on PySide2.
    QtGui.QAction = QtWidgets.QAction
    QtGui.QActionGroup = QtWidgets.QActionGroup
    QtGui.QShortcut = QtWidgets.QShortcut
else:
    # Keep Qt5-style imports working on PySide6.
    QtWidgets.QAction = QtGui.QAction
    QtWidgets.QActionGroup = QtGui.QActionGroup
    QtWidgets.QShortcut = QtGui.QShortcut
    # QRegExp / QRegExpValidator were removed in Qt6; alias to the
    # QRegularExpression equivalents so callers written against Qt5 keep working.
    QtCore.QRegExp = QtCore.QRegularExpression
    QtGui.QRegExpValidator = QtGui.QRegularExpressionValidator


# Make `from rpa.utils.qt.QtCore import X` work by registering the real
# submodules under this package's dotted path in sys.modules.
_sys.modules[__name__ + ".QtCore"] = QtCore
_sys.modules[__name__ + ".QtGui"] = QtGui
_sys.modules[__name__ + ".QtWidgets"] = QtWidgets


def _import_optional(name):
    try:
        if PYSIDE_VERSION == 6:
            mod = __import__(f"PySide6.{name}", fromlist=[name])
        else:
            mod = __import__(f"PySide2.{name}", fromlist=[name])
    except ImportError:
        return None
    _sys.modules[__name__ + "." + name] = mod
    return mod


QtOpenGL = _import_optional("QtOpenGL")
QtNetwork = _import_optional("QtNetwork")
QtWebEngineCore = _import_optional("QtWebEngineCore")
QtWebEngineWidgets = _import_optional("QtWebEngineWidgets")
QtWebChannel = _import_optional("QtWebChannel")


def get_pyside_version() -> int:
    return PYSIDE_VERSION
