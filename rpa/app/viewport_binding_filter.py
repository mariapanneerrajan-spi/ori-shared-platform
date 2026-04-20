try:
    from PySide2 import QtCore
except Exception:
    from PySide6 import QtCore


class ViewportBindingFilter(QtCore.QObject):
    """Event filter that suppresses OpenRV-native input bindings on the viewport.

    Installed on OpenRV's viewport widget (GLView) BEFORE plugin event filters
    so that it runs AFTER them (Qt calls filters in reverse installation order).
    Plugin filters process events first and return False; this filter then
    consumes targeted events so GLView::event() never translates them into
    Mu events (key-down, pointer-3--push, etc.).
    """

    _BLOCKED_TYPES = frozenset({
        QtCore.QEvent.KeyPress,
        QtCore.QEvent.KeyRelease,
        QtCore.QEvent.ShortcutOverride,
        QtCore.QEvent.Shortcut,
        QtCore.QEvent.Wheel,
        QtCore.QEvent.ContextMenu,
    })

    _MOUSE_BUTTON_TYPES = frozenset({
        QtCore.QEvent.MouseButtonPress,
        QtCore.QEvent.MouseButtonRelease,
        QtCore.QEvent.MouseButtonDblClick,
    })

    def eventFilter(self, obj, event):
        etype = event.type()

        if etype in self._BLOCKED_TYPES:
            return True

        if etype == QtCore.QEvent.MouseButtonDblClick:
            return True

        if etype in self._MOUSE_BUTTON_TYPES:
            return True

        return False
