try:
    from PySide2 import QtWidgets
except:
    from PySide6 import QtWidgets


class DropdownComboBox(QtWidgets.QComboBox):

    def __init__(self, parent=None):
        super().__init__(parent)

    def showPopup(self):
        super().showPopup()
        popup = self.view().window()
        if popup:
            popup.move(self.mapToGlobal(self.rect().bottomLeft()))
