try:
    from rpa.utils.qt import QtCore, QtGui, QtWidgets
except:
    from PySide6 import QtGui, QtCore, QtWidgets

class Actions(QtCore.QObject):
    def __init__(self):
        super().__init__()

        # FStop
        self.fstop_up = QtWidgets.QAction("Up")
        self.fstop_up.setShortcut(QtGui.QKeySequence("Ctrl+Up"))

        self.fstop_down = QtWidgets.QAction("Down")
        self.fstop_down.setShortcut(QtGui.QKeySequence("Ctrl+Down"))

        self.fstop_reset = QtWidgets.QAction("Reset")
        self.fstop_reset.setShortcut(QtGui.QKeySequence("Ctrl+Home"))

        self.fstop_pgup = QtWidgets.QAction("Up By 3")
        self.fstop_pgup.setShortcut(QtGui.QKeySequence("Ctrl+PgUp"))

        self.fstop_pgdown = QtWidgets.QAction("Down By 3")
        self.fstop_pgdown.setShortcut(QtGui.QKeySequence("Ctrl+PgDown"))

        self.fstop_slider = QtWidgets.QAction("FStop Slider")
        self.fstop_slider.setCheckable(True)

        # Gamma
        self.gamma_up = QtWidgets.QAction("Up")
        self.gamma_up.setShortcut(QtGui.QKeySequence("Alt+Up"))

        self.gamma_down = QtWidgets.QAction("Down")
        self.gamma_down.setShortcut(QtGui.QKeySequence("Alt+Down"))

        self.gamma_reset = QtWidgets.QAction("Reset")
        self.gamma_reset.setShortcut(QtGui.QKeySequence("Alt+Home"))

        self.gamma_slider = QtWidgets.QAction("Gamma Slider")
        self.gamma_slider.setCheckable(True)
