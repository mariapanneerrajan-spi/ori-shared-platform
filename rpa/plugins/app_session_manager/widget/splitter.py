from functools import partial
try:
    from rpa.utils.qt import QtCore, QtGui, QtWidgets
except:
    from PySide6 import QtCore, QtGui, QtWidgets


class SplitterHandle(QtWidgets.QSplitterHandle):
    def __init__(self, orientation, parent=None):
        super().__init__(orientation, parent)

        self.__hovered = False
        self.setMouseTracking(True)

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        if self.__hovered:
            painter.fillRect(self.rect(), QtGui.QColor('lightgray'))

    def enterEvent(self, event):
        self.__hovered = True
        self.update()

    def leaveEvent(self, event):
        self.__hovered = False
        self.update()


class Splitter(QtWidgets.QSplitter):

    PLAYLIST_PANEL_INDEX = 0
    CLIPS_TABLE_INDEX = 1

    ANIM_LENGTH = 120
    PLAYLIST_PANEL_DEFAULT_SIZE = 200

    def __init__(self, parent=None):
        super().__init__(parent)

        self.__ignore_child_event = False
        self.__opened_panel_size = Splitter.PLAYLIST_PANEL_DEFAULT_SIZE
        self.__animation = None

        self.__add_toggle_button()

        self.splitterMoved.connect(self.__splitter_moved)

    def createHandle(self):
        handle = SplitterHandle(self.orientation(), self)
        return handle

    def resizeEvent(self, event):
        self.__toggle_button.setGeometry(
            10,
            event.size().height() - self.__toggle_button.height() - 10,
            self.__toggle_button.width(),
            self.__toggle_button.height())
        return super().resizeEvent(event)

    def childEvent(self, event):
        if self.__ignore_child_event:
            return

        super().childEvent(event)

    def __add_toggle_button(self):
        self.__ignore_child_event = True

        self.__toggle_button = QtWidgets.QPushButton(
            parent=self,
            geometry=QtCore.QRect(0, 0, 26, 26),
            icon=self.style().standardIcon(QtWidgets.QStyle.SP_ArrowRight))
        self.__toggle_button.clicked.connect(self.__toggle_left_pane)

        self.__ignore_child_event = False

    def handle_restored_state(self):
        vertical_tab_size = self.sizes()[Splitter.PLAYLIST_PANEL_INDEX]
        self.__update_icons(vertical_tab_size)

        if self.sizes()[0] != 0:
            self.__opened_panel_size = vertical_tab_size
        else:
            self.__opened_panel_size = \
                Splitter.PLAYLIST_PANEL_DEFAULT_SIZE

    def set_state(self, state):
        if state:
            self.restoreState(state)
        else:
            self.setSizes([0, 1])
        self.handle_restored_state()

    def __update_icons(self, size):
        if size == 0:
            self.__toggle_button.setIcon(
                self.style().standardIcon(QtWidgets.QStyle.SP_ArrowRight))
            self.__toggle_button.setToolTip('Show playlist panel')
        else:
            self.__toggle_button.setIcon(
                self.style().standardIcon(QtWidgets.QStyle.SP_ArrowLeft))
            self.__toggle_button.setToolTip('Hide playlist panel')

    def _get_panel_size(self):
        return self.sizes()[Splitter.PLAYLIST_PANEL_INDEX]

    def _set_panel_size(self, size):
        total = sum(self.sizes())
        self.setSizes([size, total - size])
        self.__update_icons(size)

    panel_size = QtCore.Property(int, _get_panel_size, _set_panel_size)

    def __toggle_left_pane(self):
        cur_sizes = self.sizes()

        # Remember the current open size before closing
        if cur_sizes[Splitter.PLAYLIST_PANEL_INDEX] != 0 and \
            cur_sizes[Splitter.PLAYLIST_PANEL_INDEX] != self.__opened_panel_size:
            self.__opened_panel_size = cur_sizes[Splitter.PLAYLIST_PANEL_INDEX]

        if cur_sizes[Splitter.PLAYLIST_PANEL_INDEX] == 0:
            target_size = self.__opened_panel_size
        else:
            target_size = 0

        # Stop any running animation
        if self.__animation is not None:
            self.__animation.stop()

        self.__animation = QtCore.QPropertyAnimation(self, b"panel_size")
        self.__animation.setDuration(Splitter.ANIM_LENGTH)
        self.__animation.setStartValue(cur_sizes[Splitter.PLAYLIST_PANEL_INDEX])
        self.__animation.setEndValue(target_size)
        self.__animation.setEasingCurve(QtCore.QEasingCurve.OutCubic)
        self.__animation.finished.connect(self.__splitter_moved)
        self.__animation.start()

    def __splitter_moved(self):
        sizes = self.sizes()
        self.__update_icons(sizes[0])

        playlist_panel_size = sizes[Splitter.PLAYLIST_PANEL_INDEX]
        if playlist_panel_size > 0:
            # In order to not save the size as increasingly smaller
            # as the user drags the splitter closed, use a timer
            # to delay the save.
            QtCore.QTimer.singleShot(100, \
                partial(self.__save_opened_panel_size, playlist_panel_size))

    def __save_opened_panel_size(self, size):
        """Remember this size if the size is still the same."""
        sizes = self.sizes()
        if len(sizes) < Splitter.PLAYLIST_PANEL_INDEX:
            return
        playlist_panel_size = sizes[Splitter.PLAYLIST_PANEL_INDEX]
        if playlist_panel_size != size:
            # Size has changed; don't save.
            return
        self.__opened_panel_size = playlist_panel_size
