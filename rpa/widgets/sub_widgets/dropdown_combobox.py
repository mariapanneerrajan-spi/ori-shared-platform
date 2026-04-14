try:
    from PySide2 import QtCore, QtWidgets
except:
    from PySide6 import QtCore, QtWidgets


class DropdownComboBox(QtWidgets.QComboBox):

    def __init__(self, parent=None):
        super().__init__(parent)

    def showPopup(self):
        super().showPopup()
        popup = self.view().window()
        if popup:
            popup.move(self.mapToGlobal(self.rect().bottomLeft()))


class ComboBoxWithTooltip(DropdownComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.installEventFilter(self)
        self.tooltips = {}

    def addItem(self, text, tooltip=""):
        super().addItem(text)
        self.tooltips[text] = tooltip

    def eventFilter(self, obj: QtCore.QObject, event: QtCore.QEvent):
        if obj == self and event.type() == QtCore.QEvent.ToolTip:
            index = self.view().indexAt(event.pos())
            if index.isValid():
                text = self.itemText(index.row())
                if text in self.tooltips:
                    QtWidgets.QToolTip.showText(
                        event.globalPos(), self.tooltips[text], self)
            return True
        return super().eventFilter(obj, event)
