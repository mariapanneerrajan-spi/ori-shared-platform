"""Itview's main window.

Constructed with the OpenRV viewport widget (GLView, a QOpenGLWidget),
which is re-parented into the central widget under a custom menu bar.
The OpenRV main window (RvDocument) is hidden separately by the caller
but kept alive — GLView holds a raw C++ pointer to RvDocument and would
crash if RvDocument were deleted.
"""

import ctypes
import platform

try:
    from PySide2 import QtWidgets
except ImportError:
    from PySide6 import QtWidgets


class ItviewMainWindow(QtWidgets.QMainWindow):

    def __init__(self, viewport_widget, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Itview")

        self._viewport_widget = viewport_widget
        # Some plugins reach for `_core_view` as an attribute. Kept alongside
        # get_core_view() so both access patterns work.
        self._core_view = viewport_widget

        # The viewport is the central widget directly — no intermediate
        # container. setCentralWidget reparents the widget into this window,
        # which (like setParent) hides it, so we re-show it explicitly.
        # Without this, the central area looks empty.
        self.setCentralWidget(self._viewport_widget)
        self._viewport_widget.show()

        # Itview menus that plugins attach actions to. Added straight to the
        # QMainWindow's built-in menu bar — plugins that need the menu bar
        # itself can call self.menuBar() directly. The first menu is
        # historically named "Itview" rather than "File".
        self._file_menu = self.menuBar().addMenu("Itview")
        self._session_menu = self.menuBar().addMenu("Session")
        self._plugins_menu = self.menuBar().addMenu("Plugins")

        self._enable_dark_title_bar()

    def _enable_dark_title_bar(self):
        """Use the dark title bar on Windows 10/11. No-op on other platforms."""
        if platform.system() != 'Windows':
            return
        try:
            hwnd = int(self.winId())
            DWMWA_USE_IMMERSIVE_DARK_MODE = 20
            value = ctypes.c_int(1)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE,
                ctypes.byref(value), ctypes.sizeof(value))
        except Exception:
            pass

    # --- Plugin manager / plugin contract ----------------------------------
    # These methods (and toggle_fullscreen below) are the public surface that
    # the plugin manager and individual plugins call on the main window.

    def get_core_view(self):
        return self._viewport_widget

    def get_file_menu(self):
        return self._file_menu

    def get_session_menu(self):
        return self._session_menu

    def get_plugins_menu(self):
        return self._plugins_menu

    def toggle_fullscreen(self):
        """Called by the view_controller plugin (was provided by RvDocument)."""
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()
