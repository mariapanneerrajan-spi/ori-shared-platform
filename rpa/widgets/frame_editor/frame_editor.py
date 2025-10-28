from PySide2 import QtCore, QtGui, QtWidgets
from rpa.utils.validators import NumValidator


class FrameLabel(QtWidgets.QLabel):

    def __init__(self, prefix="", parent=None):
        super().__init__(parent)

        self.prefix = prefix
        self.value = ""
        self.__update_text()

    def update_value(self, value):
        self.value = str(value)
        self.__update_text()
    
    def __update_text(self):
        self.setText(f"{self.prefix}: <b>{self.value}</b>")


class FrameSpinBox(QtWidgets.QSpinBox):

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setMinimum(1)
        self.setMaximum(100)


class FrameEditor(QtWidgets.QWidget):

    def __init__(self, rpa, main_window, parent=None):
        super().__init__(parent)

        self.__rpa = rpa
        self.__main_window = main_window

        self.__session_api = self.__rpa.session_api
        self.__timeline_api = self.__rpa.timeline_api

        self.__init_ui()
        self.__connect_signals()


    def __init_ui(self):
        self.setWindowTitle("Frame Editor")

        self.main_widget = QtWidgets.QWidget()
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.addWidget(self.main_widget)
        self.main_layout.setContentsMargins(1, 1, 1, 1)
        self.setLayout(self.main_layout)

        # TIMELINE FRAMES
        self.__seq_frame_label = FrameLabel("Sequence Frame")
        self.__clip_frame_label = FrameLabel("Clip Frame")

        self.__header_widget = QtWidgets.QWidget()
        self.__header_layout = QtWidgets.QVBoxLayout()
        self.__header_layout.setAlignment(QtCore.Qt.AlignCenter)
        self.__header_layout.addWidget(self.__seq_frame_label)
        self.__header_layout.addWidget(self.__clip_frame_label)
        self.__header_widget.setLayout(self.__header_layout)

        # FRAME CONTROL
        self.__prev_frame_button = QtWidgets.QPushButton("<", self)
        self.__prev_frame_button.setToolTip("Previous Frame")
        self.__prev_frame_button.setFixedSize(QtCore.QSize(30, 30))
        
        self.__next_frame_button = QtWidgets.QPushButton(">", self)
        self.__next_frame_button.setToolTip("Next Frame")
        self.__next_frame_button.setFixedSize(QtCore.QSize(30, 30))

        self.__frame_edit = QtWidgets.QLineEdit('', self)
        self.__frame_edit.setFixedSize(QtCore.QSize(100, 30))
        self.__frame_edit.setValidator(NumValidator(self))
        self.__frame_edit.setFocusPolicy(QtCore.Qt.StrongFocus)

        self.__frame_widget = QtWidgets.QWidget()
        self.__frame_layout = QtWidgets.QHBoxLayout()
        self.__frame_layout.setAlignment(QtCore.Qt.AlignCenter)
        self.__frame_layout.addWidget(self.__prev_frame_button)
        self.__frame_layout.addWidget(self.__frame_edit)
        self.__frame_layout.addWidget(self.__next_frame_button)
        self.__frame_widget.setLayout(self.__frame_layout)

        # HOLD
        self.__hold_button = QtWidgets.QPushButton("Hold", self)
        self.__hold_button.setToolTip("Hold Frames")
        self.__hold_button.setFocusPolicy(QtCore.Qt.NoFocus)

        self.__hold_spinbox = FrameSpinBox(self)
        
        self.__hold_widget = QtWidgets.QWidget()
        self.__hold_layout = QtWidgets.QHBoxLayout()
        self.__hold_layout.setAlignment(QtCore.Qt.AlignCenter)
        self.__hold_layout.addWidget(self.__hold_spinbox)
        self.__hold_layout.addWidget(self.__hold_button)
        self.__hold_widget.setLayout(self.__hold_layout)

        # DROP
        self.__drop_button = QtWidgets.QPushButton("Drop", self)
        self.__drop_button.setToolTip("Drop Frames")
        self.__drop_button.setFocusPolicy(QtCore.Qt.NoFocus)

        self.__drop_spinbox = FrameSpinBox(self)

        self.__drop_widget = QtWidgets.QWidget()
        self.__drop_layout = QtWidgets.QHBoxLayout()
        self.__drop_layout.setAlignment(QtCore.Qt.AlignCenter)
        self.__drop_layout.addWidget(self.__drop_spinbox)
        self.__drop_layout.addWidget(self.__drop_button)
        self.__drop_widget.setLayout(self.__drop_layout)

        # RESET
        self.__reset_button = QtWidgets.QPushButton("Reset", self)
        self.__reset_button.setToolTip("Reset Frame Edits")
        self.__reset_button.setFocusPolicy(QtCore.Qt.NoFocus)

        # CLOSE
        self.__close_button = QtWidgets.QPushButton("Close", self)
        self.__close_button.setToolTip("Close AnimEdit Light")
        self.__close_button.setFocusPolicy(QtCore.Qt.NoFocus)

        self.__footer_widget = QtWidgets.QWidget()
        self.__footer_layout = QtWidgets.QHBoxLayout()
        self.__footer_layout.addStretch()
        self.__footer_layout.addWidget(self.__reset_button)
        self.__footer_layout.addWidget(self.__close_button)
        self.__footer_widget.setLayout(self.__footer_layout)

        # LAYOUT
        self.main_layout.addWidget(self.__header_widget)
        self.main_layout.addWidget(self.__frame_widget)
        self.main_layout.addWidget(self.__hold_widget)
        self.main_layout.addWidget(self.__drop_widget)
        self.main_layout.addWidget(self.__footer_widget)

    def __connect_signals(self):
        self.__timeline_api.SIG_FRAME_CHANGED.connect(self.__timeline_frame_changed)
        self.__timeline_api.SIG_MODIFIED.connect(self.__timeline_modified)
        self.__session_api.SIG_CURRENT_CLIP_CHANGED.connect(self.__current_clip_changed)

        self.__prev_frame_button.clicked.connect(lambda: self.__step_frame(-1))
        self.__next_frame_button.clicked.connect(lambda: self.__step_frame(1))
        self.__frame_edit.returnPressed.connect(self.__change_frame)
        self.__hold_button.clicked.connect(self.__hold_frames)
        self.__drop_button.clicked.connect(self.__drop_frames)
        self.__reset_button.clicked.connect(self.reset_frames)
        self.__close_button.clicked.connect(self.__close)

    def reconnect_signals(self):
        self.__timeline_api.SIG_FRAME_CHANGED.connect(self.__timeline_frame_changed)
        self.__timeline_api.SIG_MODIFIED.connect(self.__timeline_modified)
        self.__timeline_modified()

    def disconnect_signals(self):
        self.__timeline_api.SIG_FRAME_CHANGED.disconnect(self.__timeline_frame_changed)
        self.__timeline_api.SIG_MODIFIED.disconnect(self.__timeline_modified)

    def __timeline_modified(self):
        clip_id = self.__session_api.get_current_clip()
        if clip_id is None:
            self.__reset_all_values()
            return
        
        self.__current_clip_changed(clip_id)

    def __current_clip_changed(self, clip_id):
        if clip_id is None:
            self.__reset_all_values()
            return
        current_frame = self.__timeline_api.get_current_frame()
        seq_frames = self.__timeline_api.get_seq_frames(clip_id)

        if seq_frames:
            seq_frames_only = [f for _, seqs in seq_frames for f in seqs]
            if current_frame in seq_frames_only:
                self.__set_all_values(current_frame)
            else:
                self.__set_all_values(1)

    def __timeline_frame_changed(self, frame):
        playing, forward = self.__timeline_api.get_playing_state()
        if playing:
            return
        
        clip_id = self.__session_api.get_current_clip()
        if clip_id is None:
            self.__reset_all_values()
            return
        
        self.__set_all_values(frame)

    def __set_all_values(self, frame):
        if frame is not None:
            current_seq_frame = frame
            current_clip_frame = None
            
            [clip_frame] = self.__timeline_api.get_clip_frames([current_seq_frame])
            clip_id, current_clip_frame, local_frame = clip_frame
            tw_in = self.__session_api.get_attr_value(clip_id, "timewarp_in")
            key_in = self.__session_api.get_attr_value(clip_id, "key_in")
            if tw_in is not None:
                current_tw_frame = tw_in + local_frame - 1
            else:
                current_tw_frame = key_in + local_frame - 1

            if None not in (current_seq_frame, current_clip_frame, current_tw_frame):
                self.__seq_frame_label.update_value(current_seq_frame)
                self.__clip_frame_label.update_value(current_clip_frame)
                self.__frame_edit.setText(str(current_tw_frame))

    def __reset_all_values(self):
        self.__seq_frame_label.update_value("")
        self.__clip_frame_label.update_value("")
        self.__frame_edit.setText("")

    def __step_frame(self, step:int):
        if not step in (1, -1):
            return

        clip_id = self.__session_api.get_current_clip()
        if not clip_id:
            return

        current_frame = self.__timeline_api.get_current_frame()
        new_frame = current_frame + step

        seq_frames = self.__timeline_api.get_seq_frames(clip_id)
        seq_frames_only = [f for _, seqs in seq_frames for f in seqs]

        min_seq_frame = min(seq_frames_only)
        max_seq_frame = max(seq_frames_only)

        if new_frame < min_seq_frame:
            new_frame = max_seq_frame
        elif new_frame > max_seq_frame:
            new_frame = min_seq_frame

        self.__timeline_api.goto_frame(new_frame)

    def __change_frame(self):
        frame_edit_value = int(self.__frame_edit.text().strip())

        clip_id = self.__session_api.get_current_clip()
        frame_in = self.__session_api.get_attr_value(clip_id, "timewarp_in")
        frame_out = self.__session_api.get_attr_value(clip_id, "timewarp_out")
        
        if None in (frame_in, frame_out):
            frame_in = self.__session_api.get_attr_value(clip_id, "key_in")
            frame_out = self.__session_api.get_attr_value(clip_id, "key_out")

        if frame_edit_value < frame_in:
            frame_edit_value = frame_in
        elif frame_edit_value > frame_out:
            frame_edit_value = frame_out

        record_frame = frame_edit_value - frame_in + 1
        
        self.__frame_edit.setText(str(frame_edit_value))
        self.__timeline_api.goto_frame(record_frame)
        

    def __hold_frames(self):
        hold_value = int(self.__hold_spinbox.value())
        clip_id = self.__session_api.get_current_clip()
        current_frame = self.__timeline_api.get_current_frame()

        current_clip_frame = self.__timeline_api.get_clip_frames([current_frame])
        if current_clip_frame:
            [current_clip_frame] = current_clip_frame
            clip_frame = current_clip_frame[1]
            print("clip_frame", clip_frame, "hold_value", hold_value)
            self.__session_api.edit_frames(clip_id, 1, clip_frame, hold_value)

    def __drop_frames(self):
        drop_value = self.__drop_spinbox.value()
        clip_id = self.__session_api.get_current_clip()
        current_frame = self.__timeline_api.get_current_frame()

        current_clip_frame = self.__timeline_api.get_clip_frames([current_frame])
        if current_clip_frame:
            [current_clip_frame] = current_clip_frame
            clip_frame = current_clip_frame[1]
            print("clip_frame", clip_frame, "drop_value", drop_value)
            self.__session_api.edit_frames(clip_id, -1, clip_frame, drop_value)

    def reset_frames(self):
        clip_id = self.__session_api.get_current_clip()
        self.__session_api.reset_frames(clip_id)

    def __close(self):
        dock_widget = self.parentWidget()
        if dock_widget:
            dock_widget.close()
            self.disconnect_signals()
