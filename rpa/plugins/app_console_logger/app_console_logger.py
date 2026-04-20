"""Console Logger plugin entry point.

Installs process-wide interception hooks for Python print output (via a
sys.stdout / sys.stderr tee) and RPA log records (via a logging.Handler on
``logging.getLogger("rpa")``). Both destinations are additive — the terminal
still receives prints and ``rpa.log`` still receives log records.

This plugin is registered first in ``open_app_plugins.cfg`` so its hooks
are installed before subsequent plugins' ``app_init`` runs, allowing their
early output to be captured.
"""
import sys
import logging

from PySide2 import QtCore, QtGui
from rpa.app.widgets.itv_dock_widget import ItvDockWidget

from app_console_logger.log_bridge import (
    LogBridge, QtLogHandler, StreamTee)
from app_console_logger.console_view import ConsoleView


class AppConsoleLogger(QtCore.QObject):

    def __init__(self):
        super().__init__()
        self.__bridge = None
        self.__log_handler = None
        self.__stdout_tee = None
        self.__stderr_tee = None
        self.__view = None
        self.__dock = None
        self.__main_window = None

    def app_init(self, rpa_app):
        self.__main_window = rpa_app.main_window

        # 1. Signal bridge + view
        self.__bridge = LogBridge()
        self.__view = ConsoleView()
        self.__bridge.SIG_ENTRY.connect(
            self.__view.append_entry,
            QtCore.Qt.QueuedConnection)  # thread-safe marshaling

        # 2. Dock widget and menu toggle
        self.__dock = ItvDockWidget("Console Logger", self.__main_window)
        self.__dock.setWidget(self.__view)
        self.__main_window.addDockWidget(
            QtCore.Qt.BottomDockWidgetArea, self.__dock)
        self.__dock.hide()

        self.__toggle_action = self.__dock.toggleViewAction()
        self.__toggle_action.setShortcut(QtGui.QKeySequence("Ctrl+`"))
        self.__toggle_action.setProperty("hotkey_editor", True)
        plugins_menu = self.__main_window.get_menu("Plugins")
        plugins_menu.addAction(self.__toggle_action)

        # 3. Attach logging handler to the RPA logger.
        # The existing RotatingFileHandler stays — this is additive.
        rpa_logger = logging.getLogger("rpa")
        self.__log_handler = QtLogHandler(self.__bridge)
        self.__log_handler.setFormatter(logging.Formatter("%(message)s"))
        rpa_logger.addHandler(self.__log_handler)

        # 4. Tee sys.stdout / sys.stderr so prints reach both the terminal
        # and the console widget.
        self.__stdout_tee = StreamTee(sys.stdout, self.__bridge, "STDOUT")
        self.__stderr_tee = StreamTee(sys.stderr, self.__bridge, "STDERR")
        sys.stdout = self.__stdout_tee
        sys.stderr = self.__stderr_tee

        # 5. Clean up on shutdown so a subsequent session starts fresh.
        self.__main_window.destroyed.connect(self.__shutdown)

    def __shutdown(self):
        # Restore original streams if we are still the installed tee.
        try:
            if sys.stdout is self.__stdout_tee and self.__stdout_tee is not None:
                sys.stdout = self.__stdout_tee.original
        except Exception:
            pass
        try:
            if sys.stderr is self.__stderr_tee and self.__stderr_tee is not None:
                sys.stderr = self.__stderr_tee.original
        except Exception:
            pass
        try:
            if self.__log_handler is not None:
                logging.getLogger("rpa").removeHandler(self.__log_handler)
        except Exception:
            pass
