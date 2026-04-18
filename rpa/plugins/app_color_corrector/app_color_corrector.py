from PySide2 import QtCore, QtGui, QtWidgets
from rpa.widgets.color_corrector.controller import Controller
from rpa.app.skin.widgets.itv_dock_widget import ItvDockWidget


class AppColorCorrector(QtCore.QObject):

    def __init__(self):
        super().__init__()

    def app_init(self, rpa_app):
        self.__rpa = rpa_app.rpa
        self.__main_window = rpa_app.main_window

        self.__color_api = self.__rpa.color_api
        self.__color_corrector = Controller(self.__rpa, self.__main_window)

        self.__dock_widget = ItvDockWidget("Color Corrector", self.__main_window)
        self.__dock_widget.setWidget(self.__color_corrector.view)
        self.__main_window.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.__dock_widget)
        self.__dock_widget.hide()

        self.__toggle_action = self.__dock_widget.toggleViewAction()
        self.__toggle_action.setShortcut(QtGui.QKeySequence("F9"))
        self.__toggle_action.setProperty("hotkey_editor", True)

        review_menu = self.__main_window.get_menu("Review")
        review_menu.addSeparator()
        review_menu.addAction(self.__toggle_action)
        review_menu.addSeparator()
