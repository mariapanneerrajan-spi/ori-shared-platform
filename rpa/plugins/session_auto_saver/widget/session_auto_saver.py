from typing import List
try:
    from rpa.utils.qt import QtCore, QtGui, QtWidgets
    from rpa.utils.qt.QtWidgets import QAction
except:
    from PySide6 import QtCore, QtGui, QtWidgets
    from PySide6.QtGui import QAction
import os
import glob
from datetime import datetime
from rpa_widgets.session_io.otio_reader import OTIOReader
from rpa_widgets.session_io.otio_writer import OTIOWriter
from session_auto_saver.widget.auto_save_browser import AutoSaveBrowser


class AutoSavePopup(QtWidgets.QDialog):
    SIG_PREF_CHANGED = QtCore.Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Session Restore")
        self.setModal(True)
        self.setMinimumWidth(420)
        self.__result = QtWidgets.QMessageBox.No

        message = QtWidgets.QLabel(
            "RPA session was not closed properly last time. "
            "Would you like to restore the auto saved session?")
        message.setWordWrap(True)

        check_box = QtWidgets.QCheckBox("Don't show this message again.")
        check_box.toggled.connect(self.SIG_PREF_CHANGED)

        menu_msg = QtWidgets.QLabel(
            "Auto saved sessions can also be restored from "
            "the Session Auto Saver widget.")
        menu_msg.setWordWrap(True)
        menu_msg.setEnabled(False)

        yes_btn = QtWidgets.QPushButton("Yes")
        no_btn = QtWidgets.QPushButton("No")
        no_btn.setDefault(True)
        yes_btn.clicked.connect(self.__accept)
        no_btn.clicked.connect(self.reject)

        btn_layout = QtWidgets.QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(yes_btn)
        btn_layout.addWidget(no_btn)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(message)
        layout.addSpacing(8)
        layout.addWidget(check_box)
        layout.addWidget(menu_msg)
        layout.addSpacing(4)
        layout.addLayout(btn_layout)

    def __accept(self):
        self.__result = QtWidgets.QMessageBox.Yes
        self.accept()

    def result(self):
        return self.__result

def _styled_msg_dialog(parent, title, text):
    dlg = QtWidgets.QDialog(parent)
    dlg.setWindowTitle(title)
    dlg.setModal(True)
    label = QtWidgets.QLabel(text)
    label.setWordWrap(True)
    ok_btn = QtWidgets.QPushButton("OK")
    ok_btn.setDefault(True)
    ok_btn.clicked.connect(dlg.accept)
    btn_layout = QtWidgets.QHBoxLayout()
    btn_layout.addStretch()
    btn_layout.addWidget(ok_btn)
    layout = QtWidgets.QVBoxLayout(dlg)
    layout.addWidget(label)
    layout.addSpacing(8)
    layout.addLayout(btn_layout)
    return dlg


def _styled_confirm_dialog(parent, title, text):
    dlg = QtWidgets.QDialog(parent)
    dlg.setWindowTitle(title)
    dlg.setModal(True)
    label = QtWidgets.QLabel(text)
    label.setWordWrap(True)
    ok_btn = QtWidgets.QPushButton("OK")
    no_btn = QtWidgets.QPushButton("No")
    no_btn.setDefault(True)
    ok_btn.clicked.connect(dlg.accept)
    no_btn.clicked.connect(dlg.reject)
    btn_layout = QtWidgets.QHBoxLayout()
    btn_layout.addStretch()
    btn_layout.addWidget(ok_btn)
    btn_layout.addWidget(no_btn)
    layout = QtWidgets.QVBoxLayout(dlg)
    layout.addWidget(label)
    layout.addSpacing(8)
    layout.addLayout(btn_layout)
    return dlg


class SessionAutoSaver(QtWidgets.QWidget):

    def __init__(self, rpa, main_window, auto_save_directory=None, include_feedback=True, hide_checkbox=False):
        super().__init__(main_window)
        self.__rpa = rpa
        self.__main_window = main_window
        self.__auto_save_directory = auto_save_directory
        if self.__auto_save_directory is None:
            self.__auto_save_directory = os.path.expanduser("~")

        self.__otio_reader = OTIOReader(self.__rpa, main_window, include_feedback)
        self.__otio_writer = OTIOWriter(self.__rpa, main_window, include_feedback)
        self.__dont_show_auto_save_popup_pref_key = "dont_show_auto_save_popup"

        self.__auto_save_browser = AutoSaveBrowser(self.__main_window)
        self.__auto_save_browser.SIG_FILE_SELECTED.connect(self.__file_selected)

        self.__auto_save_file_name_prefix = "auto_save_rpa_session"
        self.__pid = os.getpid()
        self.__auto_save_file = os.path.join(
            self.__auto_save_directory,
            f"{self.__auto_save_file_name_prefix}_{self.__pid}.otio")

        self.__timer = QtCore.QTimer(self)
        self.__timer.timeout.connect(self.__save_session)

        dont_show_auto_save_popup_box_pref = self.__rpa.config_api.value(
            self.__dont_show_auto_save_popup_pref_key, False, type=bool)
        self.__dont_show_auto_save_popup_chk_box = \
            QtWidgets.QCheckBox("Don't Show Auto Save Popup")
        self.__dont_show_auto_save_popup_chk_box.setChecked(
            dont_show_auto_save_popup_box_pref)
        self.__dont_show_auto_save_popup_chk_box.toggled.connect(
            self.__update_dont_show_auto_save_popup_pref)

        self.__auto_save_state_chk_box = \
            QtWidgets.QCheckBox("Pause Auto Save")
        self.__auto_save_state_chk_box.toggled.connect(
            self.__set_auto_save_state)

        auto_save_path_label = QtWidgets.QLabel("Auto Save Path:")
        auto_save_path_line_edit = QtWidgets.QLineEdit()
        auto_save_path_line_edit.setText(self.__auto_save_file)
        auto_save_path_line_edit.setReadOnly(True)
        auto_save_path_layout = QtWidgets.QHBoxLayout()
        auto_save_path_layout.addWidget(auto_save_path_label)
        auto_save_path_layout.addWidget(auto_save_path_line_edit)

        last_saved_label = QtWidgets.QLabel("Last Saved:")
        self.__last_saved_line_edit = QtWidgets.QLineEdit()
        self.__last_saved_line_edit.setText(self.__auto_save_file)
        self.__last_saved_line_edit.setReadOnly(True)
        self.__last_saved_line_edit.setText("Not Yet Saved!")
        self.__last_saved_line_edit.setToolTip(
            "Auto saves every 1 minute, "
            "if timeline is not playing clips.")
        last_saved_layout = QtWidgets.QHBoxLayout()
        last_saved_layout.addWidget(last_saved_label)
        last_saved_layout.addWidget(self.__last_saved_line_edit)

        load_prev_auto_saves_btn = QtWidgets.QPushButton("Load Previous Auto Saves")
        load_prev_auto_saves_btn.clicked.connect(self.__load_prev_auto_saves)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.__dont_show_auto_save_popup_chk_box)
        layout.addWidget(self.__auto_save_state_chk_box)
        layout.addLayout(auto_save_path_layout)
        layout.addLayout(last_saved_layout)
        layout.addWidget(load_prev_auto_saves_btn)
        layout.addSpacerItem(
            QtWidgets.QSpacerItem(
                0, 0, QtWidgets.QSizePolicy.Minimum,
                QtWidgets.QSizePolicy.Expanding))
        self.setLayout(layout)

        main_window.installEventFilter(self)

        auto_saves = self.__get_auto_saves()
        if auto_saves and not dont_show_auto_save_popup_box_pref and not hide_checkbox:
            auto_save_popup = AutoSavePopup(main_window)
            auto_save_popup.SIG_PREF_CHANGED.connect(
                self.__update_dont_show_auto_save_popup_pref)
            auto_save_popup.SIG_PREF_CHANGED.connect(
                self.__update_dont_show_auto_save_popup_checkbox_state)
            auto_save_popup.exec()
            if auto_save_popup.result() == QtWidgets.QMessageBox.Yes:
                playlist_ids = self.__rpa.session_api.get_playlists() # default playlist
                latest_auto_save = max(auto_saves, key=os.path.getmtime)
                success = self.__otio_reader.read_otio_file(latest_auto_save)
                if success:
                    self.__rpa.session_api.delete_playlists_permanently(playlist_ids)

        self.__timer.start(60 * 1000)  # 1 minute in milliseconds

    def __update_dont_show_auto_save_popup_checkbox_state(self, state):
        self.__dont_show_auto_save_popup_chk_box.blockSignals(True)
        self.__dont_show_auto_save_popup_chk_box.setChecked(state)
        self.__dont_show_auto_save_popup_chk_box.blockSignals(False)

    def __update_dont_show_auto_save_popup_pref(self, state):
        self.__rpa.config_api.setValue(
            self.__dont_show_auto_save_popup_pref_key, state)

    def __save_session(self):
        is_playing, _ = self.__rpa.timeline_api.get_playing_state()
        if not is_playing:
            playlist_ids = self.__rpa.session_api.get_playlists()
            self.__otio_writer.write_to_file(playlist_ids, self.__auto_save_file)
            current_time = datetime.now().strftime("%H:%M:%S")
            self.__last_saved_line_edit.setText(current_time)

    def __set_auto_save_state(self, state):
        if state and self.__timer.isActive(): self.__timer.stop()
        else: self.__timer.start()

    def __load_prev_auto_saves(self):
        auto_saves = self.__get_auto_saves()
        if not auto_saves:
            msg_box = _styled_msg_dialog(
                self.__main_window, "Info",
                "No auto saved session exists!")
            msg_box.exec()
        else:
            self.__auto_save_browser.populate_files(self.__get_auto_saves())
            self.__auto_save_browser.exec()

    def __get_auto_saves(self):
        autosaves = glob.glob(
            f"{self.__auto_save_directory}"\
            f"{os.path.sep}"\
            f"{self.__auto_save_file_name_prefix}_*.otio")
        return autosaves

    def eventFilter(self, obj, event):
        if event.type() == QtCore.QEvent.Close: self.__close_event()
        return False

    def __close_event(self):
        self.__timer.stop()
        self.__remove_auto_saves()

    def __remove_auto_saves(self):
        for file in self.__get_auto_saves():
            if os.path.exists(file): os.remove(file)

    def __file_selected(self, file):
        msg_box = _styled_confirm_dialog(
            self.__main_window, "Warning",
            "Are you sure you want to replace the current session with "
            "the auto saved session?")
        result = msg_box.exec()
        if result == QtWidgets.QDialog.Accepted:
            playlist_ids = self.__rpa.session_api.get_playlists() # default playlist
            success = self.__otio_reader.read_otio_file(file)
            if success:
                self.__rpa.session_api.delete_playlists_permanently(playlist_ids)