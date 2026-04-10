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
import ctypes
import logging
import types
from logging.handlers import RotatingFileHandler
from rpa.rpa import Rpa
from itview.skin.plugin_manager.controller import Controller as PluginManager
from itview import plugin_path_configs
from itview.skin.dbid_mapper import DbidMapper
from itview.core.viewport_user_input_rx import ViewportUserInputRx
from rpa.utils import default_connection_maker
from itview.skin.itview_palette import ItviewPalette


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

        # Phase 1 prototype: instead of stripping OpenRV's main window, build a
        # fresh Itview QMainWindow and re-parent only the viewport widget into
        # it. See plans/humble-meandering-sutherland.md for the rationale and
        # the GL-context risk we're validating here.
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

        # Modes and key bindings live on RvSession, not on the window. Clear
        # them so OpenRV's defaults don't leak into Itview.
        # commands.deactivateMode("annotate_mode")
        # commands.deactivateMode("session_manager")
        # commands.clearSession()
        # commands.setCursor(0)
        # for binding in commands.bindings():
        #     commands.unbind("default", "global", binding[0])

        # Hide OpenRV's main window but keep it ALIVE. GLView holds a raw C++
        # pointer (m_doc) to RvDocument; deleting RvDocument would dangle that
        # pointer and crash on the next render. Hiding is enough to keep all
        # of OpenRV's stock UI (menus, toolbars, hotkeys) out of Itview.
        # self.__rv_main_window.hide()

        # Build the new Itview main window and re-parent the viewport into it.
        self.__main_window = QtWidgets.QMainWindow()
        self.__main_window.setWindowTitle("Itview")

        container = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._itview_menu_bar = QtWidgets.QMenuBar()
        layout.addWidget(self._itview_menu_bar)

        # The moment of truth: re-parenting a QOpenGLWidget across top-level
        # windows can trigger a GL context destroy/recreate. If the viewport
        # goes black, playback fails, or textures vanish after this point,
        # see Phase 1 fallback options in the plan file.
        self._viewport_widget.setParent(container)
        layout.addWidget(self._viewport_widget)
        # QWidget.setParent() sets the widget's visibility to false, and
        # addWidget() does NOT re-show a widget that was hidden by setParent().
        # Without this explicit show(), the viewport sits inside the layout
        # but is invisible — the central area looks empty.
        self._viewport_widget.show()

        self.__main_window.setCentralWidget(container)

        self.__setup_rpa_mode()

        self.__main_window.show()

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
        # Viewport widget was already located and re-parented in
        # __rv_session_initialized — nothing to do here for it.
        app = QtWidgets.QApplication.instance()
        app.setPalette(ItviewPalette())

        # Enable dark title bar on Windows
        if platform.system() == 'Windows':
            try:
                hwnd = int(self.__main_window.winId())
                DWMWA_USE_IMMERSIVE_DARK_MODE = 20
                value = ctypes.c_int(1)
                ctypes.windll.dwmapi.DwmSetWindowAttribute(
                    hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE,
                    ctypes.byref(value), ctypes.sizeof(value))
            except Exception:
                pass

        app.setStyleSheet("""
            QDockWidget {
                border: none;
            }
            QDockWidget::title {
                background: palette(window);
                border-bottom: 1px solid palette(dark);
                padding: 4px;
            }
            QToolBar {
                border: none;
                spacing: 2px;
            }
            QTableView, QListView, QTreeView {
                border: 1px solid palette(dark);
            }
            QSplitter::handle {
                background: palette(dark);
            }
            QHeaderView {
                background: palette(window);
                border: none;
            }
            QHeaderView::section {
                background: palette(window);
                color: palette(window-text);
                border: none;
                border-right: 1px solid palette(dark);
                border-bottom: 1px solid palette(dark);
                padding: 4px 6px;
            }
            QHeaderView::section:hover {
                background: palette(midlight);
            }
            QTableView QTableCornerButton::section {
                background: palette(window);
                border: none;
                border-right: 1px solid palette(dark);
                border-bottom: 1px solid palette(dark);
            }
            QTableView::item:selected {
                background: palette(highlight);
            }
            QHeaderView QToolButton {
                background: palette(window);
                border: none;
                padding: 2px;
            }
            QHeaderView QToolButton:hover {
                background: palette(midlight);
            }
            QMenuBar {
                background: palette(window);
                color: palette(window-text);
                border-bottom: 1px solid palette(dark);
            }
            QMenuBar::item {
                background: transparent;
                padding: 4px 8px;
            }
            QMenuBar::item:selected {
                background: palette(highlight);
            }
            QMenu {
                background: palette(window);
                color: palette(window-text);
                border: 1px solid palette(dark);
            }
            QMenu::item:selected {
                background: palette(highlight);
            }
            QTabBar::tab {
                background: palette(dark);
                color: palette(window-text);
                border: 1px solid palette(dark);
                padding: 4px 10px;
            }
            QTabBar::tab:selected {
                background: palette(window);
                border-bottom: none;
            }
            QTabBar::tab:hover {
                background: palette(midlight);
            }
            QTabWidget::pane {
                border: 1px solid palette(dark);
                background: palette(window);
            }
            QScrollBar:vertical {
                background: palette(base);
                width: 12px;
                border: none;
            }
            QScrollBar::handle:vertical {
                background: palette(midlight);
                min-height: 20px;
                border-radius: 3px;
                margin: 2px;
            }
            QScrollBar::handle:vertical:hover {
                background: palette(light);
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar:horizontal {
                background: palette(base);
                height: 12px;
                border: none;
            }
            QScrollBar::handle:horizontal {
                background: palette(midlight);
                min-width: 20px;
                border-radius: 3px;
                margin: 2px;
            }
            QScrollBar::handle:horizontal:hover {
                background: palette(light);
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
            }
            QToolTip {
                background: palette(base);
                color: palette(window-text);
                border: 1px solid palette(dark);
                padding: 2px;
            }
            QLineEdit {
                background: palette(base);
                color: palette(window-text);
                border: 1px solid palette(dark);
                border-radius: 2px;
                padding: 2px 4px;
            }
            QLineEdit:focus {
                border: 1px solid palette(highlight);
            }
            QComboBox {
                background: palette(base);
                color: palette(window-text);
                border: 1px solid palette(dark);
                border-radius: 2px;
                padding: 2px 6px;
            }
            QComboBox:hover {
                border: 1px solid palette(midlight);
            }
            QComboBox QAbstractItemView {
                background: palette(base);
                color: palette(window-text);
                border: 1px solid palette(dark);
                selection-background-color: palette(highlight);
            }
            QComboBox::drop-down {
                border: none;
                background: palette(window);
            }
            QSpinBox, QDoubleSpinBox {
                background: palette(base);
                color: palette(window-text);
                border: 1px solid palette(dark);
                border-radius: 2px;
                padding: 2px 4px;
            }
            QSpinBox:focus, QDoubleSpinBox:focus {
                border: 1px solid palette(highlight);
            }
            QSpinBox::up-button, QDoubleSpinBox::up-button,
            QSpinBox::down-button, QDoubleSpinBox::down-button {
                background: palette(window);
                border: none;
            }
            QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
            QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {
                background: palette(midlight);
            }
            QPushButton {
                background: palette(window);
                color: palette(window-text);
                border: 1px solid palette(dark);
                border-radius: 2px;
                padding: 4px 8px;
            }
            QPushButton:hover {
                background: palette(midlight);
            }
            QPushButton:pressed {
                background: palette(dark);
            }
            QTextEdit, QPlainTextEdit {
                background: palette(base);
                color: palette(window-text);
                border: 1px solid palette(dark);
            }
            QCheckBox::indicator {
                width: 14px;
                height: 14px;
                border: 1px solid palette(dark);
                border-radius: 2px;
                background: palette(base);
            }
            QCheckBox::indicator:checked {
                background: palette(highlight);
            }
            QSlider::groove:horizontal {
                background: palette(dark);
                height: 4px;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: palette(light);
                width: 12px;
                margin: -4px 0;
                border-radius: 6px;
            }
            QSlider::handle:horizontal:hover {
                background: palette(window-text);
            }
            QSlider::groove:vertical {
                background: palette(dark);
                width: 4px;
                border-radius: 2px;
            }
            QSlider::handle:vertical {
                background: palette(light);
                height: 12px;
                margin: 0 -4px;
                border-radius: 6px;
            }
            QSlider::sub-page:horizontal {
                background: palette(highlight);
                border-radius: 2px;
            }
            QToolButton {
                background: transparent;
                border: none;
                padding: 2px;
            }
            QToolButton:hover {
                background: palette(midlight);
                border-radius: 2px;
            }
            QToolButton:pressed {
                background: palette(dark);
            }
        """)
        self.__rpa_core = app.rpa_core

        self._file_menu = self._itview_menu_bar.addMenu("Itview")
        self._session_menu = self._itview_menu_bar.addMenu("Session")
        self._plugins_menu = self._itview_menu_bar.addMenu("Plugins")

        self.__main_window.get_core_view = types.MethodType(lambda self: self._viewport_widget, self)
        self.__main_window.get_itview_menu_bar = types.MethodType(lambda self: self._itview_menu_bar, self)
        self.__main_window.get_file_menu = types.MethodType(lambda self: self._file_menu, self)
        self.__main_window.get_session_menu = types.MethodType(lambda self: self._session_menu, self)
        self.__main_window.get_plugins_menu = types.MethodType(lambda self: self._plugins_menu, self)
        # view_controller plugin calls toggle_fullscreen() on the main window.
        # Used to be provided by RvDocument; now we own the window so we
        # implement it ourselves.
        self.__main_window.toggle_fullscreen = self._toggle_fullscreen

        logger = create_logger()
        plugin_manager = \
            PluginManager(self.__main_window, plugin_path_configs.get(), logger)

        self.__rpa = Rpa(create_config(self.__main_window), logger)
        default_connection_maker.set_core_delegates_for_all_rpa(
            self.__rpa, self.__rpa_core)

        self.__rpa.session_api.get_attrs_metadata()
        self.__rpa_core.viewport_api._set_viewport_widget(self._viewport_widget)
        self.__main_window._core_view = self._viewport_widget
        self.__rpa.session_api.clear()

        dbid_mapper = DbidMapper()
        self.__viewport_user_input = ViewportUserInputRx()
        self.__viewport_user_input.set_viewport_widget(
            self._viewport_widget)
        plugin_manager.init(self.__rpa, dbid_mapper, self.__viewport_user_input)

        # No event filters needed: OpenRV's main window is hidden so its stock
        # toolbars/menus/dock widgets never become visible, and the viewport
        # double-click handler in eventFilter was already a no-op.

    def _toggle_fullscreen(self):
        if self.__main_window.isFullScreen():
            self.__main_window.showNormal()
        else:
            self.__main_window.showFullScreen()

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
