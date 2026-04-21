from rpa.utils.qt import QtCore, QtGui


class NumValidator(QtGui.QRegExpValidator):
    def __init__(self, parent=None):
        super().__init__(QtCore.QRegExp("-?\\d+"), parent)


class FloatValidator(QtGui.QRegExpValidator):
    def __init__(self, parent=None):
        super().__init__(QtCore.QRegExp("\\.\\d+|\\d+(\\.\\d*)?"), parent)


class RatValidator(QtGui.QRegExpValidator):
    def __init__(self, parent=None):
        super().__init__(QtCore.QRegExp("\\.\\d+|\\d+(\\.\\d*)?|\\d+((\+\\d+)?/\\d+)?"), parent)


class FStopValidator(QtGui.QDoubleValidator):
    def __init__(self, parent=None):
        super().__init__(self, -10, 10, 2, parent)

class FPSValidator(QtGui.QDoubleValidator):
    def __init__(self, parent=None):
        super().__init__(self, 1.0, 24.0 * 64.0, 3, parent)