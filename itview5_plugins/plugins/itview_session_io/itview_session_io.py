import os
from PySide2 import QtCore, QtGui, QtWidgets
from PySide2.QtWidgets import QAction
from rpa.widgets.session_io.session_io import SessionIO


class ItviewSessionIO(QtCore.QObject):

    def itview_init(self, itview):
        self.__rpa = itview.rpa
        self.__main_window = itview.main_window
        self.__session_io = SessionIO(
            self.__rpa, self.__main_window, feedback=True)

        self.__session_io.append_session_action.setShortcut(
            QtGui.QKeySequence("Ctrl+O"))
        self.__session_io.replace_session_action.setShortcut(
            QtGui.QKeySequence("Ctrl+Alt+O"))
        self.__session_io.save_session_action.setShortcut(
            QtGui.QKeySequence("Ctrl+S"))

        self.__session_io.append_session_action.setProperty("hotkey_editor", True)
        self.__session_io.replace_session_action.setProperty("hotkey_editor", True)
        self.__session_io.save_session_action.setProperty("hotkey_editor", True)
        self.__session_io.core_preferences_action.setProperty("hotkey_editor", True)
        self.__session_io.clear_session_action.setProperty("hotkey_editor", True)

        file_menu = self.__main_window.get_file_menu()

        self.__add_clips_action = QAction("Add Clips", parent=self.__main_window)
        self.__add_clips_action.triggered.connect(lambda: self.__add_clips())
        file_menu.addAction(self.__add_clips_action)

        file_menu.addSeparator()
        file_menu.addAction(self.__session_io.append_session_action)
        file_menu.addAction(self.__session_io.replace_session_action)
        file_menu.addSeparator()
        file_menu.addAction(self.__session_io.save_session_action)
        file_menu.addSeparator()
        file_menu.addAction(self.__session_io.core_preferences_action)
        file_menu.addSeparator()
        file_menu.addAction(self.__session_io.clear_session_action)

    def __add_clips(self):
        paths, what = QtWidgets.QFileDialog.getOpenFileNames(
            self.__main_window,
            "Open Media",
            "",
            "",
            options=QtWidgets.QFileDialog.DontUseNativeDialog)
        if len(paths) == 0:
            return

        fg_playlist = self.__rpa.session_api.get_fg_playlist()
        selected_clips = \
            self.__rpa.session_api.get_active_clips(fg_playlist)
        if len(selected_clips) == 0:
            self.__rpa.session_api.create_clips(fg_playlist, paths)
        else:
            last_selected_clip = selected_clips[-1]
            clips = self.__rpa.session_api.get_clips(fg_playlist)
            index = clips.index(last_selected_clip) + 1
            self.__rpa.session_api.create_clips(fg_playlist, paths, index)
