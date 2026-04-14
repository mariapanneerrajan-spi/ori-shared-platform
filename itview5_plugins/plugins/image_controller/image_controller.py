from PySide2 import QtCore
from rpa.widgets.image_controller.image_controller import ImageController as RpaImageController


class ImageController(QtCore.QObject):

    def __init__(self):
        super().__init__()

    def itview_init(self, itview):
        self.__rpa = itview.rpa
        self.__main_window = itview.main_window
        self.__cmd_line_args = itview.cmd_line_args

        self.__image_controller = RpaImageController(self.__rpa, self.__main_window)

        self.__create_menu()

        self.__image_controller.actions.fstop_up.setProperty("hotkey_editor", True)
        self.__image_controller.actions.fstop_down.setProperty("hotkey_editor", True)
        self.__image_controller.actions.fstop_reset.setProperty("hotkey_editor", True)
        self.__image_controller.actions.fstop_pgup.setProperty("hotkey_editor", True)
        self.__image_controller.actions.fstop_pgdown.setProperty("hotkey_editor", True)
        self.__image_controller.actions.gamma_up.setProperty("hotkey_editor", True)
        self.__image_controller.actions.gamma_down.setProperty("hotkey_editor", True)
        self.__image_controller.actions.gamma_reset.setProperty("hotkey_editor", True)

    def __create_menu(self):
        color_menu = self.__main_window.get_menu("Color")

        # FStop
        fstop_menu = color_menu.addMenu("FStop")
        fstop_menu.addAction(self.__image_controller.actions.fstop_up)
        fstop_menu.addAction(self.__image_controller.actions.fstop_down)
        fstop_menu.addAction(self.__image_controller.actions.fstop_reset)
        fstop_menu.addAction(self.__image_controller.actions.fstop_pgup)
        fstop_menu.addAction(self.__image_controller.actions.fstop_pgdown)
        fstop_menu.addSeparator()
        fstop_menu.addAction(self.__image_controller.actions.fstop_slider)

        # Gamma
        gamma_menu = color_menu.addMenu("Gamma")
        gamma_menu.addAction(self.__image_controller.actions.gamma_up)
        gamma_menu.addAction(self.__image_controller.actions.gamma_down)
        gamma_menu.addAction(self.__image_controller.actions.gamma_reset)
        gamma_menu.addSeparator()
        gamma_menu.addAction(self.__image_controller.actions.gamma_slider)
