from rpa.utils.qt import QtCore, QtWidgets, QtGui
from rpa.app.widgets.itv_dock_widget import ItvDockWidget
from help_menu.about import AboutDialog
import os

USER_DOCUMENTATION = "https://sonyimageworks.atlassian.net/wiki/spaces/Dev/pages/1466302863/App+-+Getting+Started+-+User+Guide"
RPA_DOCUMENTATION = "http://docs.spimageworks.com/projects/gitprod/rpa_app-plugins/rpa/docs/build/html/index.html"

class HelpMenu(QtCore.QObject):
    def __init__(self):
        super().__init__()

    def app_init(self, rpa_app):
        self.__main_window = rpa_app.main_window
        self.__toggle_rpa_interpretter_action = None
        self.__app_version = os.getenv("SPK_PKG_rpa_app_VERSION", "Unable to detect version")
        self.__rpa_version = os.getenv("SPK_OPT_rpa_app.rpa", "Unable to detect version")
        self.__about_dialog = AboutDialog("App", rpa_app_version=self.__app_version,
                                          rpa_version=self.__rpa_version, parent=self.__main_window)

        self.__user_documentation = QtWidgets.QAction("User Documentation")
        self.__user_documentation.triggered.connect(lambda: self.__open_link(USER_DOCUMENTATION))
        self.__rpa_documentation = QtWidgets.QAction("RPA Documentation")
        self.__rpa_documentation.triggered.connect(lambda: self.__open_link(RPA_DOCUMENTATION))
        self.__about = QtWidgets.QAction("About")
        self.__about.triggered.connect(self.__open_about_dialog)

        self.__create_menu()

    def __create_menu(self):
        self.help_menu = self.__main_window.menuBar().addMenu("Help")
        self.help_menu.addAction(self.__user_documentation)
        self.help_menu.addAction(self.__rpa_documentation)
        self.help_menu.addAction(self.__about)

    def __open_link(self, link):
        url = QtCore.QUrl(link)
        QtGui.QDesktopServices.openUrl(url)

    def post_app_init(self):
        dock = self.__main_window.findChild(ItvDockWidget, "Rpa Interpreter")
        if dock:
            self.__toggle_rpa_interpretter_action = dock.toggleViewAction()
            self.help_menu.addAction(self.__toggle_rpa_interpretter_action)

    def __open_about_dialog(self):
        self.__about_dialog.show()
