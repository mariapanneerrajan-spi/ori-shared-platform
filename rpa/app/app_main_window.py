"""App's main window.

Constructed with a viewport widget supplied by the caller, which is
re-parented into the central widget under a custom menu bar. App is
deliberately agnostic to which review system provided that viewport —
shutdown of the underlying review system is coordinated via the
SIG_CLOSED signal, which the review-system-specific glue listens to.
"""

import ctypes
import platform

try:
    from PySide2 import QtWidgets
    from PySide2.QtCore import Signal
except ImportError:
    from PySide6 import QtWidgets
    from PySide6.QtCore import Signal


# Bump when dock widget objectNames or the layout structure change in a
# backwards-incompatible way; restoreState() will silently discard saved
# state with a different version instead of applying a broken layout.
_STATE_VERSION = 1


class AppMainWindow(QtWidgets.QMainWindow):

    # Emitted from closeEvent, before the event is forwarded to the base
    # class. Review-system-specific glue (e.g. the RV mode) connects to this
    # to tear down the underlying review system's own main window/session.
    # Kept as a plain signal with no args so App stays decoupled from any
    # particular review system.
    SIG_CLOSED = Signal()

    def __init__(self, viewport_widget, settings=None, logger=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("App")

        # Shared QSettings / logger passed in by the review-system glue. The
        # same QSettings object is injected into Rpa so App and RPA share
        # one on-disk file. `settings` is used to persist window geometry and
        # dock/toolbar layout across sessions; `logger` is accepted for
        # symmetry with Rpa and kept available for future use.
        self._settings = settings
        self._logger = logger
        self._layout_restored = False

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

        # App menus that plugins attach actions to. Added straight to the
        # QMainWindow's built-in menu bar — plugins that need the menu bar
        # itself can call self.menuBar() directly. The first menu is
        # historically named "App" rather than "File".
        self._file_menu = self.menuBar().addMenu("App")
        self._session_menu = self.menuBar().addMenu("Session")
        self._plugins_menu = self.menuBar().addMenu("Plugins")

        # Registry: name -> QMenu for all menus (pre-existing and dynamic).
        # Seeded with the three constructor menus so get_menu() returns them
        # instead of creating duplicates.
        self._menus = {
            "App": self._file_menu,
            "Session": self._session_menu,
            "Plugins": self._plugins_menu,
        }

        # Menu names that must stay at the right end of the menu bar.
        # Dynamic menus created via get_menu() are inserted before these.
        self._tail_menu_names = {"Plugins", "Help"}

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

    def get_menu(self, name):
        """Return the QMenu named *name*, creating it on demand.

        Pre-existing menus ("App", "Session", "Plugins") are returned
        from the cache. New menus are inserted before the first tail menu
        ("Plugins", "Help") so the bar stays: … dynamic menus … Plugins Help.
        """
        menu = self._menus.get(name)
        if menu is not None:
            return menu

        # Find the first tail-menu action in the bar to insert before.
        before_action = None
        for action in self.menuBar().actions():
            if action.text() in self._tail_menu_names:
                before_action = action
                break

        new_menu = QtWidgets.QMenu(name, self)
        if before_action is not None:
            self.menuBar().insertMenu(before_action, new_menu)
        else:
            self.menuBar().addMenu(new_menu)

        self._menus[name] = new_menu
        return new_menu

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

    def showEvent(self, event):
        """Restore saved layout on the first show.

        By the time Qt fires showEvent, the plugin manager has already run
        and every plugin dock widget has been added to this window — so
        restoreState() can match saved entries against each dock widget's
        objectName(). Guarded by _layout_restored so later show/hide
        cycles (e.g. toggling fullscreen) don't re-apply the saved state
        on top of the user's in-session adjustments.
        """
        super().showEvent(event)
        if not self._layout_restored:
            self._layout_restored = True
            self._restore_layout()

    def closeEvent(self, event):
        """Notify listeners that App is closing, then proceed.

        Emits SIG_CLOSED so the review-system-specific glue can shut down
        the underlying review system (e.g. close RvDocument so OpenRV
        actually quits — without this it lingers as a hidden window).
        Signal emission is synchronous, so listeners have run by the time
        we forward to the base class.

        Layout is saved *before* SIG_CLOSED is emitted, while the window
        is still fully intact — the signal triggers review-system teardown
        which may reparent or destroy dock widgets.
        """
        self._save_layout()
        self.SIG_CLOSED.emit()
        super().closeEvent(event)

    # --- Layout persistence ------------------------------------------------

    def _save_layout(self):
        """Persist window geometry and dock/toolbar layout to settings.

        Keys are written relative to whatever group the shared QSettings
        already has active (the injector sets up the top-level "rpa_app"
        group), so on disk these end up as "rpa_app/window/geometry" and
        "rpa_app/window/state".
        """
        if self._settings is None:
            return
        self._settings.setValue("window/geometry", self.saveGeometry())
        self._settings.setValue(
            "window/state", self.saveState(_STATE_VERSION))

    def _restore_layout(self):
        """Restore window geometry and dock/toolbar layout from settings.

        Silently does nothing if no state has been saved yet (first launch)
        or if the saved state version doesn't match _STATE_VERSION.
        """
        if self._settings is None:
            return
        geometry = self._settings.value("window/geometry")
        if geometry is not None:
            self.restoreGeometry(geometry)
        state = self._settings.value("window/state")
        if state is not None:
            self.restoreState(state, _STATE_VERSION)
