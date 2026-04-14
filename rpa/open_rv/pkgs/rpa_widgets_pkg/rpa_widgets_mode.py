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
import types
from logging.handlers import RotatingFileHandler
from rpa.rpa import Rpa
from itview.skin.plugin_manager.controller import Controller as PluginManager
from itview import plugin_path_configs
from itview.skin.dbid_mapper import DbidMapper
from itview.core.viewport_user_input_rx import ViewportUserInputRx
from rpa.utils import default_connection_maker


def create_config(main_window):
    config = QtCore.QSettings("imageworks.com", "rpa", main_window)
    config.beginGroup("rpa")
    return config


def create_logger():
    if platform.system() == 'Windows':
        log_dir = os.path.join(os.environ["APPDATA"], "rpa")
    elif platform.system() == 'Linux' or platform.system() == 'Darwin':
        log_dir = os.path.join(os.environ["HOME"], ".rpa")
    else:
        raise Exception("Unsupported platform!")

    if not os.path.exists(log_dir):
        os.mkdir(log_dir)
    log_filepath = os.path.join(log_dir, "rpa.log")

    logger = logging.getLogger("rpa")
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
    logger.info("[RPA] RPA Logger Created")
    return logger


class RpaWidgetsMode(QtCore.QObject, rvtypes.MinorMode):

    def __init__(self):

        QtCore.QObject.__init__(self)
        rvtypes.MinorMode.__init__(self)

        self.init(
            "RpaWidgetsMode",
            [("session-initialized", self.__rv_session_initialized, "")],
            None
        )

    def __rv_session_initialized(self, event):
        event.reject()
        self.__main_window = rv.qtutils.sessionWindow()
        self.__main_window.menuBar().setObjectName("rv_menu_bar")
        # self.__main_window.menuBar().hide()

        old_central = self.__main_window.centralWidget()
        container = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._itview_menu_bar = QtWidgets.QMenuBar()

        layout.addWidget(self._itview_menu_bar)
        layout.addWidget(old_central)

        self.__main_window.setCentralWidget(container)

        self.__strip_rv_main_window()
        self.__setup_rpa_mode()

    def eventFilter(self, object, event):
        if isinstance(object, QtWidgets.QMenuBar) and \
        object.objectName() == "rv_menu_bar" and \
        event.type() == QtCore.QEvent.Paint:
            self.__strip_rv_menu_bar(object)

        if isinstance(object, QtWidgets.QToolBar) and \
        object.objectName() in ["topToolBar", "bottomToolBar"]:
            object.hide()

        if isinstance(object, QtWidgets.QWidget) and \
        event.type() == QtCore.QEvent.Show:
            if object.objectName() == "session_manager":
                object.hide()

        if isinstance(object, QtWidgets.QDockWidget) and \
        event.type() == QtCore.QEvent.Show and \
        hasattr(object, "widget") and \
        object.widget().objectName() == "annotationTool":
            object.hide()

        if object is self._viewport_widget:
            if event.type() == QtCore.QEvent.MouseButtonDblClick:
                # self.__add_clips()
                return True

        return False

    def __strip_rv_main_window(self):
        commands.deactivateMode("annotate_mode")
        commands.deactivateMode("session_manager")
        commands.clearSession()
        commands.setCursor(0)

        for toolbar in self.__main_window.findChildren(QtWidgets.QToolBar):
            if toolbar.objectName() in ["topToolBar", "bottomToolBar"]:
                toolbar.hide()

        for widget in self.__main_window.findChildren(QtWidgets.QWidget):
            if widget.objectName() == "session_manager":
                if widget.isVisible(): widget.hide()

        for widget in self.__main_window.findChildren(QtWidgets.QDockWidget):
            if widget.widget().objectName() == "annotationTool":
                if widget.isVisible(): widget.hide()

        for binding in commands.bindings():
            commands.unbind("default", "global", binding[0])

        self.__strip_rv_menu_bar(self.__main_window.menuBar())

    def __setup_rpa_mode(self):
        self._viewport_widget = self.__main_window.findChild(
            QtWidgets.QWidget, "no session")
        app = QtWidgets.QApplication.instance()
        self.__rpa_core = app.rpa_core

        self._file_menu = self._itview_menu_bar.addMenu("Itview")
        self._session_menu = self._itview_menu_bar.addMenu("Session")
        self._plugins_menu = self._itview_menu_bar.addMenu("Plugins")

        self.__main_window.get_core_view = types.MethodType(lambda self: self._viewport_widget, self)
        self.__main_window.get_itview_menu_bar = types.MethodType(lambda self: self._itview_menu_bar, self)
        self.__main_window.get_file_menu = types.MethodType(lambda self: self._file_menu, self)
        self.__main_window.get_session_menu = types.MethodType(lambda self: self._session_menu, self)
        self.__main_window.get_plugins_menu = types.MethodType(lambda self: self._plugins_menu, self)

        logger = create_logger()
        plugin_manager = \
            PluginManager(self.__main_window, plugin_path_configs.get(), logger)

        self.__rpa = Rpa(create_config(self.__main_window), logger)
        default_connection_maker.set_core_delegates_for_all_rpa(
            self.__rpa, self.__rpa_core)

        self.__rpa.session_api.get_attrs_metadata()
        self.__rpa_core.viewport_api._set_viewport_widget(self._viewport_widget)
        self.__rpa.session_api.clear()

        dbid_mapper = DbidMapper()
        self.__viewport_user_input = ViewportUserInputRx()
        self.__viewport_user_input.set_viewport_widget(
            self._viewport_widget)
        plugin_manager.init(self.__rpa, dbid_mapper, self.__viewport_user_input)

        app.installEventFilter(self)
        self._viewport_widget.installEventFilter(self)

    def __strip_menu_actions_recursively(self, menu):
        actions = menu.actions()[:]
        for action in actions:
            if action.menu():
                self.__strip_menu_actions_recursively(action.menu())
            action.setShortcut("")
            menu.removeAction(action)

    def __strip_rv_menu_bar(self, menu):
        for action in menu.actions():
            if action and action.text() == "Open RV":
                sub_menu = action.menu()
                sub_actions =  sub_menu.actions()[:]
                for sub_action in sub_actions:
                    if sub_action.text() in ["Preferences...", "Network..."]:
                        sub_action.setShortcut("")
                        sub_menu.removeAction(sub_action)
                    if sub_action.text() in ["Quit Open RV"]:
                        sub_action.setShortcut("")

            if action and action.text() in [
                "File", "Edit", "Control", "Tools", "Audio", "Image", "Color",
                "View", "Sequence", "Stack", "Layout", "OCIO", "Window", "Help"]:
                self.__strip_menu_actions_recursively(action.menu())
                action.setShortcut("")
                menu.removeAction(action)

            # if action and action.text() != "Open RV":
            #     menu.removeAction(action)


def createMode():
    return RpaWidgetsMode()
