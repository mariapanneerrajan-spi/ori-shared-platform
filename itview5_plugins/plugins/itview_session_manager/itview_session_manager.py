import os
from PySide2 import QtCore, QtGui, QtWidgets
from rpa.widgets.session_manager.session_manager import SessionManager
from itview.skin.widgets.itv_dock_widget import ItvDockWidget
from dataclasses import dataclass
from typing import Any

INTERACTIVE_MODE = "interactive_mode"


class ItviewSessionManager(QtCore.QObject):

    def __init__(self):
        super().__init__()

    def itview_init(self, itview):
        self.__rpa = itview.rpa
        self.__main_window = itview.main_window

        self.__settings_api = itview.settings_api
        self.__config_api = self.__rpa.config_api
        self.__session_api = self.__rpa.session_api
        self.__session_manager = SessionManager(self.__rpa, self.__main_window)

        dock_widget = \
            ItvDockWidget("Itview Session Manager", self.__main_window)
        dock_widget.setWidget(self.__session_manager.view)
        self.__main_window.addDockWidget(QtCore.Qt.BottomDockWidgetArea, dock_widget)
        # dock_widget.hide()

        self.__toggle_action = dock_widget.toggleViewAction()
        self.__toggle_action.setProperty("hotkey_editor", True)
        self.__toggle_action.setShortcut(QtGui.QKeySequence("Ctrl+P"))
        self.__add_to_session_menu()

        core_view = self.__main_window.get_core_view()
        core_view.installEventFilter(self)
        core_view.setMouseTracking(True)

        self.__session_api.SIG_CURRENT_CLIP_CHANGED.connect(
            self.__update_window_title)
        self.__session_api.delegate_mngr.add_post_delegate(
            self.__session_api.set_playlist_name,
            self.__playlist_name_changed)
        self.__main_window.destroyed.connect(
            self.__session_manager.save_preferences)
        self.__settings_api.SIG_SETTINGS_CHANGED.connect(self.__setting_changed)
    
        self.__load_preferences()

    def __setting_changed(self, setting_id:str, value: Any):
        if setting_id == f"{Pref.PLUGIN}.{Pref.CONTROL}/{Pref.CURRENT_FRAME_MODE}":
            self.__session_api.set_current_frame_mode(value)
        elif setting_id == f"{Pref.PLUGIN}.{Pref.CONTROL}/{Pref.AUTO_RENAME}":
            self.__session_manager.set_auto_rename(value)
        else:
            return

        self.__save_preferences()

    def __load_preferences(self):
        self.__config_api.beginGroup(Pref.PLUGIN)

        self.__config_api.beginGroup(Pref.CONTROL)
        current_frame_mode = self.__config_api.value(Pref.CURRENT_FRAME_MODE, 0, type=int)
        auto_rename = self.__config_api.value(Pref.AUTO_RENAME, False, type=bool)
        self.__config_api.endGroup()

        self.__config_api.endGroup()

        self.__settings_api.set_value(
            f"{Pref.PLUGIN}.{Pref.CONTROL}/{Pref.CURRENT_FRAME_MODE}", 
            current_frame_mode)
        self.__settings_api.set_value(
            f"{Pref.PLUGIN}.{Pref.CONTROL}/{Pref.AUTO_RENAME}",
            auto_rename)

    def __save_preferences(self):
        self.__config_api.beginGroup(Pref.PLUGIN)

        self.__config_api.beginGroup(Pref.CONTROL)    
        current_frame_mode = self.__settings_api.get_value(
            f"{Pref.PLUGIN}.{Pref.CONTROL}/{Pref.CURRENT_FRAME_MODE}")
        auto_rename = self.__settings_api.get_value(
            f"{Pref.PLUGIN}.{Pref.CONTROL}/{Pref.AUTO_RENAME}")

        self.__config_api.setValue(Pref.CURRENT_FRAME_MODE, current_frame_mode)
        self.__config_api.setValue(Pref.AUTO_RENAME, auto_rename)
        self.__config_api.endGroup()

        self.__config_api.endGroup()

    def __add_to_session_menu(self):
        session_menu = self.__main_window.get_menu("Session")
        actions = session_menu.actions()
        if actions:
            session_menu.insertAction(actions[0], self.__toggle_action)
        else:
            session_menu.addAction(self.__toggle_action)
        session_menu.addSeparator()

    def __playlist_name_changed(self, out, playlist_id, name):
        clip_id = self.__session_api.get_current_clip()
        self.__update_window_title(clip_id)

    def __update_main_window_title(self, title):
        if not title:
            title = "Nothing loaded"
        self.__main_window.setWindowTitle("Itview5 - %s" % (title))

    def __update_window_title(self, clip_id:str):
        if clip_id is None:
            title = None
        else:
            playlist_id = self.__session_api.get_playlist_of_clip(clip_id)
            playlist_name = self.__session_api.get_playlist_name(playlist_id)
            media_path = self.__session_api.get_attr_value(clip_id, "media_path")
            media_filename = os.path.basename(media_path)
            resolution = self.__session_api.get_attr_value(clip_id, "resolution")
            play_order = self.__session_api.get_attr_value(clip_id, "play_order")
            total = len(self.__session_api.get_clips(playlist_id))
            title = f"{playlist_name} - {media_filename} {resolution} ({play_order} of {total})"

        self.__update_main_window_title(title)

    def register_settings(self, register_settings):
        register_settings(
            namespace="Session",
            category="Session > Control",
            settings=[
                {
                    "namespace": Pref.PLUGIN,
                    "id": f"{Pref.CONTROL}/{Pref.CURRENT_FRAME_MODE}",
                    "type": "enum",
                    "default": 0,
                    "options": [
                        {"value": 0, "label": "Sync Across Playlists"},
                        {"value": 1, "label": "First Frame"},
                        {"value": 2, "label": "Per Playlist"}
                    ],
                    "title": "Current Frame Mode",
                    "description": "Control how the current frame is set when moving between different playlists.\n"
                                   "[Sync Across Playlists] - Current frame is synced across all playlists\n"
                                   "[First Frame] - Current frame defaults to first frame across all playlists\n"
                                   "[Per Playlist] - Current frame is remembered per playlist"
                },
                {
                    "namespace": Pref.PLUGIN,
                    "id": f"{Pref.CONTROL}/{Pref.AUTO_RENAME}",
                    "type": "boolean",
                    "default": False,
                    "title": "Auto-Rename Playlist",
                    "description": "Automatically enter edit mode for immediate renaming of a new playlist.\n"
                                   "This option will be only applicable to new playlists created from Session Manager"
                }
            ]
        )

@dataclass
class Pref:
    PLUGIN = "session_manager"
    CONTROL = "control"
    CURRENT_FRAME_MODE = "current_frame_mode"
    AUTO_RENAME = "auto_rename"