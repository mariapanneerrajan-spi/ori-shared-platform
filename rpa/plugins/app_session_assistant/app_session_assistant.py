from rpa.utils.qt import QtCore, QtGui
from app_session_assistant.widget.session_assistant import SessionAssistant


class AppSessionAssistant:

    def app_init(self, rpa_app):
        self.__rpa = rpa_app.rpa
        self.__main_window = rpa_app.main_window

        self.__session_assistant = SessionAssistant(self.__rpa, self.__main_window)

        self.__assign_shortcuts()
        self.__create_menu()

        self.__session_assistant.prev_playlist_action.setProperty("hotkey_editor", True)
        self.__session_assistant.next_playlist_action.setProperty("hotkey_editor", True)
        self.__session_assistant.prev_clip_action.setProperty("hotkey_editor", True)
        self.__session_assistant.next_clip_action.setProperty("hotkey_editor", True)
        self.__session_assistant.goto_prev_clip_action.setProperty("hotkey_editor", True)
        self.__session_assistant.goto_next_clip_action.setProperty("hotkey_editor", True)

    def __assign_shortcuts(self):
        self.__session_assistant.prev_playlist_action.setShortcut(
            QtGui.QKeySequence("Shift+Up"))
        self.__session_assistant.next_playlist_action.setShortcut(
            QtGui.QKeySequence("Shift+Down"))
        self.__session_assistant.prev_clip_action.setShortcut(
            QtGui.QKeySequence("PgUp"))
        self.__session_assistant.next_clip_action.setShortcut(
            QtGui.QKeySequence("PgDown"))
        self.__session_assistant.goto_prev_clip_action.setShortcut(
            QtGui.QKeySequence("Shift+Alt+pgup"))
        self.__session_assistant.goto_next_clip_action.setShortcut(
            QtGui.QKeySequence("Shift+Alt+pgdown"))

    def __create_menu(self):
        session_menu = self.__main_window.get_menu("Session")
        session_menu.addSeparator()
        session_menu.addAction(self.__session_assistant.prev_playlist_action)
        session_menu.addAction(self.__session_assistant.next_playlist_action)
        session_menu.addSeparator()
        session_menu.addAction(self.__session_assistant.prev_clip_action)
        session_menu.addAction(self.__session_assistant.next_clip_action)
        session_menu.addSeparator()
        session_menu.addAction(self.__session_assistant.goto_prev_clip_action)
        session_menu.addAction(self.__session_assistant.goto_next_clip_action)
        session_menu.addSeparator()
