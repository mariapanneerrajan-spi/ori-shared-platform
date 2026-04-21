import os
from rpa.utils.qt import QtCore
from timeline.widget.timeline import TimelineController
from dataclasses import dataclass
from typing import Any


class Timeline(QtCore.QObject):

    def __init__(self):
        super().__init__()

    def app_init(self, rpa_app):
        self.__rpa = rpa_app.rpa
        self.__main_window = rpa_app.main_window
        self.__cmd_line_args = rpa_app.cmd_line_args

        self.__timeline = TimelineController(self.__rpa, self.__main_window)

        self.__config_api = self.__rpa.config_api
        self.__settings_api = rpa_app.settings_api

        self.__create_menu()

        self.__timeline.actions.step_forward_action.setProperty("hotkey_editor", True)
        self.__timeline.actions.step_backward_action.setProperty("hotkey_editor", True)
        self.__timeline.actions.toggle_play_action.setProperty("hotkey_editor", True)
        self.__timeline.actions.toggle_play_forward_action.setProperty("hotkey_editor", True)
        self.__timeline.actions.toggle_play_backward_action.setProperty("hotkey_editor", True)
        self.__timeline.actions.toggle_mute_action.setProperty("hotkey_editor", True)
        self.__timeline.actions.toggle_audio_scrubbing_action.setProperty("hotkey_editor", True)

        self.__main_window.SIG_CLOSED.connect(self.__save_last_used_preferences)
        self.__settings_api.SIG_SETTINGS_CHANGED.connect(self.__setting_changed)

        self.__scope_last = 1
        self.__display_last = 1

    def __create_menu(self):
        # Playback
        playback_menu = self.__main_window.get_menu("Playback")
        for action in [
            self.__timeline.actions.step_backward_action,
            self.__timeline.actions.toggle_play_backward_action,
            self.__timeline.actions.toggle_play_action,
            self.__timeline.actions.toggle_play_forward_action,
            self.__timeline.actions.step_forward_action
        ]:
            playback_menu.addAction(action)
        playback_menu.addSeparator()
        playback_menu.addAction(self.__timeline.actions.playback_repeat_action)
        playback_menu.addAction(self.__timeline.actions.playback_once_action)
        playback_menu.addAction(self.__timeline.actions.playback_swing_action)
        playback_menu.addSeparator()

        playback_menu.addSeparator()
        playback_menu.addAction(self.__timeline.actions.toggle_mute_action)
        playback_menu.addAction(self.__timeline.actions.toggle_audio_scrubbing_action)
        playback_menu.addSeparator()

        dm = self.__rpa.timeline_api.delegate_mngr
        dm.add_post_delegate(self.__rpa.timeline_api.set_playback_mode, self.__set_playback_mode)

    def __set_playback_mode(self, out, mode):
        self.__timeline.actions.playback_repeat_action.setChecked(mode == 0)
        self.__timeline.actions.playback_once_action.setChecked(mode == 1)
        self.__timeline.actions.playback_swing_action.setChecked(mode == 2)

    def __load_preferences(self):
        self.__config_api.beginGroup(Pref.PLUGIN)

        self.__config_api.beginGroup(Pref.AUDIO)
        audio_volume = int(self.__config_api.value(Pref.VOLUME, 100, type=int))
        audio_volume = max(0, min(audio_volume, 100))
        mute_state = self.__config_api.value(Pref.MUTE, type=bool)
        scrubbing_state = self.__config_api.value(Pref.SCRUBBING, type=bool)
        self.__config_api.endGroup()

        self.__config_api.beginGroup(Pref.RANGE)
        scope = self.__config_api.value(Pref.SCOPE, 0, type=int)
        scope_last = self.__config_api.value(Pref.SCOPE_LAST, 1, type=int)
        display = self.__config_api.value(Pref.DISPLAY, 0, type=int)
        display_last = self.__config_api.value(Pref.DISPLAY_LAST, 1, type=int)
        self.__config_api.endGroup()

        self.__config_api.endGroup()

        self.__scope_last = scope_last
        self.__display_last = display_last

        self.__settings_api.set_value(
            f"{Pref.PLUGIN}.{Pref.RANGE}/{Pref.SCOPE}", scope)
        self.__settings_api.set_value(
            f"{Pref.PLUGIN}.{Pref.RANGE}/{Pref.DISPLAY}", display)

        self.__settings_api.set_value(
            f"{Pref.PLUGIN}.{Pref.AUDIO}/{Pref.VOLUME}", audio_volume)
        self.__settings_api.set_value(
            f"{Pref.PLUGIN}.{Pref.AUDIO}/{Pref.MUTE}", mute_state)
        self.__settings_api.set_value(
            f"{Pref.PLUGIN}.{Pref.AUDIO}/{Pref.SCRUBBING}", scrubbing_state)

    def __save_preferences(self):
        self.__config_api.beginGroup(Pref.PLUGIN)

        self.__config_api.beginGroup(Pref.AUDIO)
        audio_volume = self.__settings_api.get_value(
            f"{Pref.PLUGIN}.{Pref.AUDIO}/{Pref.VOLUME}")
        mute_state = self.__settings_api.get_value(
            f"{Pref.PLUGIN}.{Pref.AUDIO}/{Pref.MUTE}")
        scrubbing_state = self.__settings_api.get_value(
            f"{Pref.PLUGIN}.{Pref.AUDIO}/{Pref.SCRUBBING}")
        self.__config_api.setValue(Pref.VOLUME, audio_volume)
        self.__config_api.setValue(Pref.MUTE, mute_state)
        self.__config_api.setValue(Pref.SCRUBBING, scrubbing_state)
        self.__config_api.endGroup()

        self.__config_api.beginGroup(Pref.RANGE)
        scope = self.__settings_api.get_value(
            f"{Pref.PLUGIN}.{Pref.RANGE}/{Pref.SCOPE}")
        display = self.__settings_api.get_value(
            f"{Pref.PLUGIN}.{Pref.RANGE}/{Pref.DISPLAY}")
        self.__config_api.setValue(Pref.SCOPE, scope)
        self.__config_api.setValue(Pref.DISPLAY, display)
        self.__config_api.endGroup()

        self.__config_api.endGroup()

    def __save_last_used_preferences(self, pref_id:str=None):
        # save all last used prefs if pref_id is None
        self.__config_api.beginGroup(Pref.PLUGIN)

        if pref_id == Pref.SCOPE or pref_id is None:
            scope_last = self.__timeline.get_range_scope()
            self.__scope_last = scope_last
            self.__config_api.setValue(f"{Pref.RANGE}/{Pref.SCOPE_LAST}", self.__scope_last)

        if pref_id == Pref.DISPLAY or pref_id is None:
            display_last = self.__timeline.get_range_display()
            self.__display_last = display_last
            self.__config_api.setValue(f"{Pref.RANGE}/{Pref.DISPLAY_LAST}", self.__display_last)

        self.__config_api.endGroup()

    def post_app_init(self):
        self.__load_preferences()

        if self.__cmd_line_args.notimeline:
            self.__timeline.set_visible(False)

    # def add_cmd_line_args(self, parser):
    #     group = parser.add_argument_group("Timeline")
    #     group.add_argument(
    #         '--ntl', '--notimeline',
    #         action='store_true',
    #         dest='notimeline',
    #         help='Do not show timeline and playback toolbar')

    def __setting_changed(self, setting_id:str, value:Any):
        if setting_id == f"{Pref.PLUGIN}.{Pref.AUDIO}/{Pref.VOLUME}":
            self.__timeline.actions.set_volume(value)
        elif setting_id == f"{Pref.PLUGIN}.{Pref.AUDIO}/{Pref.MUTE}":
            self.__timeline.actions.toggle_mute(value)
        elif setting_id == f"{Pref.PLUGIN}.{Pref.AUDIO}/{Pref.SCRUBBING}":
            self.__timeline.actions.toggle_audio_scrubbing(value)

        elif setting_id == f"{Pref.PLUGIN}.{Pref.RANGE}/{Pref.SCOPE}":
            if value == 0 and self.__scope_last != 0:
                value = self.__scope_last
            self.__timeline.set_range_scope(value)
            self.__save_last_used_preferences(Pref.SCOPE)
        elif setting_id == f"{Pref.PLUGIN}.{Pref.RANGE}/{Pref.DISPLAY}":
            if value == 0 and self.__display_last != 0:
                value = self.__display_last
            self.__timeline.set_range_display(value)
            self.__save_last_used_preferences(Pref.DISPLAY)
        else:
            return

        self.__save_preferences()

    def register_settings(self, register_settings):
        register_settings(
            namespace="Playback",
            category="Playback > Audio",
            settings=[
                {
                    "namespace": Pref.PLUGIN,
                    "id": f"{Pref.AUDIO}/{Pref.VOLUME}",
                    "type": "integer",
                    "default": 100,
                    "minimum": 0,
                    "maximum": 100,
                    "step": 10,
                    "title": "Volume",
                    "description": "Set the audio level when the application starts"
                },
                {
                    "namespace": Pref.PLUGIN,
                    "id": f"{Pref.AUDIO}/{Pref.MUTE}",
                    "type": "boolean",
                    "default": False,
                    "title": "Mute Audio",
                    "description": "Set to mute audio when the application starts"
                },
                {
                    "namespace": Pref.PLUGIN,
                    "id": f"{Pref.AUDIO}/{Pref.SCRUBBING}",
                    "type": "boolean",
                    "default": False,
                    "title": "Play Audio While Scrubbing",
                    "description": "Set to play audio while scrubbing when the application starts"

                }
            ]
        )
        register_settings(
            namespace="Timeline",
            category="Timeline > Range",
            settings=[
                {
                    "namespace": Pref.PLUGIN,
                    "id": f"{Pref.RANGE}/{Pref.SCOPE}",
                    "type": "enum",
                    "default": 0,
                    "options": [
                        {"value": 1, "label": "Clip"},
                        {"value": 2, "label": "Sequence"},
                        {"value": 0, "label": "Remember Last"}
                    ],
                    "title": "Scope",
                    "description": "Set timeline range scope when the application starts\n"
                                   "[Remember Last] - Restore last used setting"
                },
                {
                    "namespace": Pref.PLUGIN,
                    "id": f"{Pref.RANGE}/{Pref.DISPLAY}",
                    "type": "enum",
                    "default": 0,
                    "options": [
                        {"value": 1, "label": "Frames"},
                        {"value": 2, "label": "Timecode"},
                        {"value": 3, "label": "Feet"},
                        {"value": 0, "label": "Remember Last"}
                    ],
                    "title": "Display",
                    "description": "Set timeline range display when the application starts\n"
                                   "[Remember Last] - Restore last used setting"
                },
            ]
        )

@dataclass
class Pref:
    PLUGIN = "timeline"
    AUDIO = "audio"
    VOLUME = "volume"
    MUTE = "mute"
    SCRUBBING = "scrubbing"
    RANGE = "range"
    DISPLAY = "display"
    SCOPE = "scope"
    DISPLAY_LAST = "display_last"
    SCOPE_LAST = "scope_last"
