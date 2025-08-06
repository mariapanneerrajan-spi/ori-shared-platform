from typing import List
try:
    from PySide2 import QtCore, QtWidgets
except ImportError:
    from PySide6 import QtCore, QtWidgets
import os
from rpa.widgets.session_io.otio_reader import OTIOReader
from rpa.widgets.session_io.otio_writer import OTIOWriter


class AutoSessionSaver(QtWidgets.QWidget):

    def __init__(self, rpa, main_window, autosave_path=None, feedback=True):
        super().__init__(main_window)
        self.__rpa = rpa
        self.__pid = os.getpid()

        if autosave_path is None:
            autosave_path = os.path.expanduser("~")
        self.__auto_save_file = os.join(autosave_path, f"autosave_rpa_session_{self.__pid}.otio")

        print(f"Auto session saver initialized with autosave path: {self.__auto_save_file}")

        self.__otio_reader = OTIOReader(self.__rpa, main_window, feedback)
        self.__otio_writer = OTIOWriter(self.__rpa, main_window, feedback)

        self._timer = QtCore.QTimer(self)
        self._timer.timeout.connect(self.__save_session)

    def start_auto_saving(self):
        self._timer.start(60 * 1000)  # 1 minute in milliseconds

    def save_session(self):
        is_playing, _ = self.__rpa.timeline_api.get_playing_state()
        if is_playing:
            self.__otio_writer.write_otio_file(self.__auto_save_file)
            print("Saved session to", self.__auto_save_file)
