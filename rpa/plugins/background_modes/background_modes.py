from PySide2 import QtCore, QtWidgets, QtGui
from background_modes.widget.background_modes \
    import BackgroundModes as RpaBackgroundModes
from rpa.session_state.annotations import Annotation
from rpa.session_state.color_corrections import ColorCorrection
import uuid
import os


class BackgroundModes(QtCore.QObject):

    def __init__(self):
        super().__init__()

    def app_init(self, rpa_app):
        self.__rpa = rpa_app.rpa
        self.__main_window = rpa_app.main_window

        self.__background_modes = RpaBackgroundModes(self.__rpa, self.__main_window)

        self.__background_modes.actions.pip.setProperty("hotkey_editor", True)
        self.__background_modes.actions.side_by_side.setProperty("hotkey_editor", True)
        self.__background_modes.actions.top_to_bottom.setProperty("hotkey_editor", True)
        self.__background_modes.actions.swap_background.setProperty("hotkey_editor", True)
        self.__background_modes.actions.turn_off_background.setProperty("hotkey_editor", True)

        self.__create_menu_bar()

    def __create_menu_bar(self):
        compare_menu = self.__main_window.get_menu("Compare")

        compare_menu.addAction(self.__background_modes.actions.turn_off_background)
        compare_menu.addSeparator()
        compare_menu.addAction(self.__background_modes.actions.side_by_side)
        compare_menu.addAction(self.__background_modes.actions.top_to_bottom)
        compare_menu.addAction(self.__background_modes.actions.pip)
        compare_menu.addSeparator()
        compare_menu.addAction(self.__background_modes.actions.swap_background)

        mix_modes = compare_menu.addMenu("Mix Modes")
        mix_modes.addAction(self.__background_modes.actions.none_mix_mode)
        mix_modes.addAction(self.__background_modes.actions.add_mix_mode)
        mix_modes.addAction(self.__background_modes.actions.diff_mix_mode)
        mix_modes.addAction(self.__background_modes.actions.sub_mix_mode)
        mix_modes.addAction(self.__background_modes.actions.over_mix_mode)
