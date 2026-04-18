import os
try:
    from PySide2 import QtCore, QtWidgets
    from PySide2.QtWidgets import QAction
    from PySide2.QtGui import QKeySequence
except:
    from PySide6 import QtCore, QtWidgets
    from PySide6.QtGui import QAction, QKeySequence

from rv import rvtypes, commands, runtime
import rv.qtutils
import platform
import logging
from logging.handlers import RotatingFileHandler
from rpa.rpa import Rpa
from rpa.app.skin.plugin_manager.controller import Controller as PluginManager
from rpa.app import plugin_path_configs
from rpa.app.skin.dbid_mapper import DbidMapper
from rpa.app.core.viewport_user_input_rx import ViewportUserInputRx
from rpa.app.core.viewport_binding_filter import ViewportBindingFilter
from rpa.utils import default_connection_maker
from rpa.app.skin.app_main_window import AppMainWindow
from rpa.app.skin.app_stylesheet import apply_app_styling


def create_config(parent=None):
    config = QtCore.QSettings("imageworks.com", "rpa_app", parent)
    config.beginGroup("rpa_app")
    return config


def create_logger():
    if platform.system() == 'Windows':
        log_dir = os.path.join(os.environ["APPDATA"], "rpa_app")
    elif platform.system() == 'Linux' or platform.system() == 'Darwin':
        log_dir = os.path.join(os.environ["HOME"], ".rpa_app")
    else:
        raise Exception("Unsupported platform!")

    if not os.path.exists(log_dir):
        os.mkdir(log_dir)
    log_filepath = os.path.join(log_dir, "rpa_app.log")

    logger = logging.getLogger("rpa_app")
    logger.setLevel(logging.DEBUG)
    if not logger.handlers:
        handler = RotatingFileHandler(
            log_filepath, mode="a", maxBytes= 10 * 1024 * 1024, backupCount=5)
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            "%(pathname)s %(funcName)s %(lineno)d:\n %(asctime)s %(levelname)s %(message)s\n",
            datefmt="%Y-%m-%d %H:%M:%S")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.propagate = False
    logger.info("[App] App Logger Created")
    return logger


class RpaWidgetsMode(QtCore.QObject, rvtypes.MinorMode):

    def __init__(self):

        print("Initializing RPA Widgets Mode...")

        QtCore.QObject.__init__(self)
        rvtypes.MinorMode.__init__(self)

        self.init(
            "RpaWidgetsMode",
            [("session-initialized", self.__rv_session_initialized, "")],
            None
        )

    def __rv_session_initialized(self, event):
        event.reject()
        self.__rv_main_window = rv.qtutils.sessionWindow()

        # Find OpenRV's viewport widget (GLView, a QOpenGLWidget). Its
        # objectName is set to "no session" in OpenRV's GLView constructor.
        # If a future OpenRV release renames it, fail loud — silent failure
        # here would mean a black window with no clue why.
        self._viewport_widget = self.__rv_main_window.findChild(
            QtWidgets.QWidget, "no session")
        assert self._viewport_widget is not None, (
            "Could not find OpenRV viewport widget (objectName='no session'). "
            "OpenRV may have renamed it in a newer release.")

        # Hide OpenRV's main window but keep it ALIVE. GLView holds a raw C++
        # pointer (m_doc) to RvDocument; deleting RvDocument would dangle that
        # pointer and crash on the next render. Hiding is enough to keep all
        # of OpenRV's stock UI (menus, toolbars, hotkeys) out of App.
        self.__rv_main_window.hide()

        # Shared QSettings + logger for both App and RPA. Created here
        # (before AppMainWindow) so the main window can receive them at
        # construction time and use the settings to persist its layout.
        # The same instances are reused when constructing Rpa(...) in
        # __setup_rpa_mode, so App and RPA write to one on-disk file
        # and log to one logger.
        self.__config = create_config(self)
        self.__logger = create_logger()

        # Build the App main window — re-parents the viewport internally
        # and provides the menu bar / accessor methods plugins expect.
        self.__main_window = AppMainWindow(
            self._viewport_widget,
            settings=self.__config,
            logger=self.__logger,
        )

        # App is deliberately agnostic to OpenRV, so it doesn't know how
        # to shut the underlying review system down. That's our job as the
        # RV-specific glue: when App closes, close the hidden RvDocument
        # so OpenRV's normal shutdown path runs (before-session-deletion
        # handler in RvDocument::closeEvent) and Qt's quitOnLastWindowClosed
        # takes the app down.
        self.__main_window.SIG_CLOSED.connect(self.__on_rpa_app_closed)

        self.__setup_rpa_mode()

        self.__main_window.show()
        print("RPA Widgets Mode initialized")

    def __on_rpa_app_closed(self):
        """Close the hidden RvDocument when App closes.

        Invoked via AppMainWindow.SIG_CLOSED. Closing RvDocument runs
        OpenRV's before-session-deletion handler and, since it was the
        only other top-level window, lets Qt quit the application.
        """
        if self.__rv_main_window is not None:
            self.__rv_main_window.close()

    def __setup_rpa_mode(self):
        # Window chrome (menus, dark title bar, viewport re-parenting,
        # toggle_fullscreen, get_*_menu accessors) is handled by
        # AppMainWindow itself. This method only wires up the RPA core,
        # plugin manager, and viewport input.
        app = QtWidgets.QApplication.instance()
        apply_app_styling(app)
        self.__rpa_core = app.rpa_core

        # Reuse the shared settings and logger created in
        # __rv_session_initialized so App and RPA share one on-disk
        # file and one logger.
        plugin_manager = PluginManager(
            self.__main_window, plugin_path_configs.get(), self.__logger)

        self.__rpa = Rpa(self.__config, self.__logger)
        default_connection_maker.set_core_delegates_for_all_rpa(
            self.__rpa, self.__rpa_core)

        self.__rpa.session_api.get_attrs_metadata()
        self.__rpa_core.viewport_api._set_viewport_widget(self._viewport_widget)
        self.__rpa.session_api.clear()

        # Install the binding filter on the viewport BEFORE plugins load their
        # own event filters.  Qt calls filters in reverse installation order
        # (last installed = first called), so plugin filters — installed later
        # during app_init — run before ours.  Plugins process the event and
        # return False; our filter then consumes it, preventing GLView::event()
        # from translating it into a Mu event (hotkey, popup menu, etc.).
        self.__viewport_binding_filter = ViewportBindingFilter()
        self._viewport_widget.installEventFilter(
            self.__viewport_binding_filter)

        dbid_mapper = DbidMapper()
        self.__viewport_user_input = ViewportUserInputRx()
        self.__viewport_user_input.set_viewport_widget(
            self._viewport_widget)
        plugin_manager.init(self.__rpa, dbid_mapper, self.__viewport_user_input)


def createMode():
    return RpaWidgetsMode()
