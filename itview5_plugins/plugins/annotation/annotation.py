from PySide2 import QtCore
from rpa.widgets.annotation.annotation import Annotation as RpaAnnotation
import rpa.widgets.annotation.constants as C


class Annotation(QtCore.QObject):

    def __init__(self):
        super().__init__()

    def itview_init(self, itview):
        self.__rpa = itview.rpa
        self.__main_window = itview.main_window
        self.__cmd_line_args = itview.cmd_line_args

        self.__annotation = RpaAnnotation(self.__rpa, self.__main_window)
        self.__create_menu_bar()

        self.__annotation.actions.show_annotations.setProperty("hotkey_editor", True)
        self.__annotation.actions.next_annot_frame.setProperty("hotkey_editor", True)
        self.__annotation.actions.prev_annot_frame.setProperty("hotkey_editor", True)
        self.__annotation.actions.undo.setProperty("hotkey_editor", True)
        self.__annotation.actions.redo.setProperty("hotkey_editor", True)
        self.__annotation.actions.clear_frame.setProperty("hotkey_editor", True)
        self.__annotation.actions.cycle_to_next_color.setProperty("hotkey_editor", True)

        self.__core_view = self.__main_window.get_core_view()
        self.__core_view.installEventFilter(self)

    def __create_menu_bar(self):
        review_menu = self.__main_window.get_menu("Review")
        review_menu.addSeparator()

        annotations_menu = None
        for action in review_menu.actions():
            submenu = action.menu()
            if submenu and submenu.title() == "Annotations":
                annotations_menu = submenu
                break
        if not annotations_menu:
            annotations_menu = review_menu.addMenu("Annotations")

        annotations_menu.addAction(self.__annotation.actions.clear_frame)
        annotations_menu.addSeparator()
        annotations_menu.addAction(self.__annotation.actions.undo)
        annotations_menu.addAction(self.__annotation.actions.redo)
        annotations_menu.addSeparator()

    def eventFilter(self, obj, event):
        if not (
        event.type() == QtCore.QEvent.MouseButtonPress or \
        event.type() == QtCore.QEvent.MouseMove or \
        event.type() == QtCore.QEvent.MouseButtonRelease):
            return False

        interactive_mode = None
        if event.modifiers() == QtCore.Qt.NoModifier:
            interactive_mode = self.__rpa.session_api.get_custom_session_attr(
                C.INTERACTIVE_MODE)
        if event.modifiers() == QtCore.Qt.ControlModifier:
            interactive_mode = C.INTERACTIVE_MODE_PEN
        if event.modifiers() == QtCore.Qt.ControlModifier | QtCore.Qt.ShiftModifier:
            interactive_mode = C.INTERACTIVE_MODE_HARD_ERASER
        if event.modifiers() == QtCore.Qt.ControlModifier | QtCore.Qt.AltModifier:
            interactive_mode = C.INTERACTIVE_MODE_LINE
        if event.modifiers() == QtCore.Qt.ControlModifier | QtCore.Qt.MetaModifier:
            interactive_mode = C.INTERACTIVE_MODE_MULTI_LINE

        self.__rpa.session_api.set_custom_session_attr(
            C.MODIFIER_INTERACTIVE_MODE, interactive_mode)

        return False

    def post_itview_init(self):
        print("Annotation plugin post_itview_init 1")
        print("Annotation plugin post_itview_init 2", self.__cmd_line_args)
        if self.__cmd_line_args.pencolor is not None:
            print("Annotation plugin post_itview_init 2")
            pen_color = self.__cmd_line_args.pencolor
            print("pen_color:", pen_color )
            pen_color = tuple(map(lambda x: max(0.0, min(1.0, x)), pen_color))
            self.__annotation.set_pen_color(pen_color)
