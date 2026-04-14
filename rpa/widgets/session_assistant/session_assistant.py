from typing import List
from rpa.utils import utils
try:
    from PySide2 import QtCore, QtWidgets
    from PySide2.QtWidgets import QAction
except:
    from PySide6 import QtCore, QtWidgets
    from PySide6.QtGui import QAction


class SessionAssistant(QtCore.QObject):
    def __init__(self, rpa, main_window):
        super().__init__()
        self.__main_window = main_window
        self.__rpa = rpa
        self.__session_api = rpa.session_api
        self.__timeline_api = rpa.timeline_api
        self.__actions = []

        self.__init_actions()
        self.__connect_signals()

    def __init_actions(self):
        self.prev_playlist_action = QAction("Prev Playlist")
        self.next_playlist_action = QAction("Next Playlist")
        self.prev_clip_action = QAction("Prev Clip")
        self.next_clip_action = QAction("Next Clip")
        self.goto_prev_clip_action = QAction("Prev Clip (Same Frame)")
        self.goto_next_clip_action = QAction("Next Clip (Same Frame)")

        self.__actions = [self.prev_playlist_action,
                          self.next_playlist_action,
                          self.prev_clip_action,
                          self.next_clip_action,
                          self.goto_prev_clip_action,
                          self.goto_next_clip_action]

    def __connect_signals(self):
        self.prev_playlist_action.triggered.connect(
            self.__goto_prev_playlist)
        self.next_playlist_action.triggered.connect(
            self.__goto_next_playlist)
        self.prev_clip_action.triggered.connect(
            lambda: utils.goto_prev_clip(self.__rpa))
        self.next_clip_action.triggered.connect(
            lambda: utils.goto_next_clip(self.__rpa))
        self.goto_prev_clip_action.triggered.connect(
            self.__goto_prev_clip)
        self.goto_next_clip_action.triggered.connect(
            self.__goto_next_clip)

    @property
    def actions(self):
        return self.__actions

    def __goto_prev_playlist(self):
        self.__goto_playlist(-1)

    def __goto_next_playlist(self):
        self.__goto_playlist(1)

    def __goto_playlist(self, offset:int):
        playlist_id = self.__session_api.get_fg_playlist()
        playlist_ids = self.__session_api.get_playlists()
        current_index = playlist_ids.index(playlist_id)

        new_playlist_id = \
            utils.get_offset_id(playlist_ids, current_index, offset)

        if playlist_id != new_playlist_id:
            self.__session_api.set_fg_playlist(new_playlist_id)

    def __goto_prev_clip(self):
        """ Jumps to the previous clip in the same playlist
            but stays on the same frame. """
        self.__move(offset=-1)

    def __goto_next_clip(self):
        """ Jumps to the next clip in the same playlist
            but stays on the same frame. """
        self.__move(offset=1)

    def __move(self, offset=1):
        """ Move to the clip based on offset from the current clip and retain the same
            frame number as the current clip. If the frame number doesnt exist, set either the
            first or last frame accordingly.
        """
        if offset not in (-1, +1):
            raise RuntimeError("Not implemented")

        playlist_id = self.__session_api.get_fg_playlist()
        if playlist_id is None: return
        clips = self.__session_api.get_active_clips(playlist_id)
        _set_active = False
        if len(clips) == 1:
            # only one clip of many is active.
            # make the neighbour clip active.
            _set_active = True
            clips = self.__session_api.get_clips(playlist_id)
        current_clip = self.__session_api.get_current_clip()
        if current_clip is None: return
        current_seq_frame = self.__timeline_api.get_current_frame()
        current_clip_frame = \
            self.__timeline_api.get_clip_frames([current_seq_frame])[0][1]

        index = clips.index(current_clip)
        target_index = (index + offset) % len(clips)
        target_clip = clips[target_index]

        # Ensure the frame stays the same as the current clip.
        first_frame = \
            self.__session_api.get_attr_value(target_clip, "key_in")
        last_frame = \
            self.__session_api.get_attr_value(target_clip, "key_out")
        if current_clip_frame > last_frame:
            current_clip_frame = last_frame
        if current_clip_frame < first_frame:
            current_clip_frame = first_frame
        if _set_active:
            # We set the target clip as an active clip.
            # This needs to be done before calling set_cuurrent_clip, otherwise
            # the frame gets reset to first frame.
            self.__session_api.set_active_clips(playlist_id, [target_clip])
        self.__session_api.set_current_clip(target_clip, frame=current_clip_frame)