from PySide2 import QtCore, QtGui, QtWidgets


class EditorialStation(QtCore.QObject):

    def __init__(self, rpa, main_window):
        self.__rpa = rpa
        self.__main_window = main_window

        self.__session_api = self.__rpa.session_api
        self.__timeline_api = self.__rpa.timeline_api

        self.__create_actions()

    def __create_actions(self):
        self.key_in_to_current_frame_action = \
            QtWidgets.QAction("Key In to Current Frame")
        self.key_out_to_current_frame_action = \
            QtWidgets.QAction("Key Out to Current Frame")
        
        self.key_in_to_current_frame_action.triggered.connect(
            self.__set_key_in_to_current_frame)
        self.key_out_to_current_frame_action.triggered.connect(
            self.__set_key_out_to_current_frame)

    def __set_key_in_to_current_frame(self):
        clip_id = self.__session_api.get_current_clip()
        if clip_id is None:
            return

        self.__set_new_key(clip_id, "key_in")

    def __set_key_out_to_current_frame(self):
        clip_id = self.__session_api.get_current_clip()
        if clip_id is None:
            return

        self.__set_new_key(clip_id, "key_out")

    def __set_new_key(self, clip_id:str, attr_id:str):
        playlist_id = self.__session_api.get_playlist_of_clip(clip_id)
        start = self.__session_api.get_attr_value(clip_id, "media_start_frame")
        end = self.__session_api.get_attr_value(clip_id, "media_end_frame")

        cur_seq_frame = self.__timeline_api.get_current_frame()
        [clip_frame] = self.__timeline_api.get_clip_frames([cur_seq_frame])
        if clip_frame and clip_frame[0] != clip_id:
            return
        clip_id, cur_clip_frame, local_frame = clip_frame

        if attr_id == "key_in":
            comparison_key = start
        elif attr_id == "key_out":
            comparison_key = end
        else:
            return

        if cur_clip_frame == comparison_key:
            return

        cur_key = \
            self.__session_api.get_attr_value(clip_id, attr_id)

        if cur_key < start:
            new_key = start
        elif cur_key > end:
            new_key = end
        elif cur_clip_frame == cur_key:
            new_key = comparison_key
        else:
            new_key = cur_clip_frame

        self.__session_api.set_attr_values(
            [(playlist_id, clip_id, attr_id, new_key)])

        if attr_id == "key_in":
            goto_frame = 1
        elif attr_id == "key_out":
            seq_frame = self.__timeline_api.get_seq_frames(clip_id, [new_key])
            if seq_frame:
                (clip_frame, [goto_frame]) = seq_frame[0]
            else:
                goto_frame = 1
        else:
            return
        self.__timeline_api.goto_frame(goto_frame)
