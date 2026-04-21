from rpa.utils.qt import QtCore, QtGui, QtWidgets
from rpa_widgets.sub_widgets.slider_toolbar import SliderToolBar
from view_controller.actions import Actions
import math


# Use to quantize float zoom level to nearest power-of-two
_FLT_MIN = 0.0000001
def _round_up_pow2(f):
    """
    Helper function to calculate closest power of 2 if f is rounded up
    :param f: value to round up
    :type f: float
    :return: rounded up to power of 2. If overflow happens, return f
    :rtype: float
    """
    try:
        return 2.0 ** math.ceil(math.log(f) / math.log(2) + _FLT_MIN)
    except OverflowError:
        return f


def _round_down_pow2(f):
    """
    Helper function to calculate closest power of 2 if f is rounded down
    :param f: value to round down
    :type f: float
    :return: rounded down to power of 2. If overflow happens, return f
    :rtype: float
    """
    try:
        return 2.0 ** math.floor(math.log(f) / math.log(2) - _FLT_MIN)
    except OverflowError:
        return f

INTERACTIVE_MODE = "interactive_mode"
INTERACTIVE_MODE_MOVE = "move"
INTERACTIVE_MODE_TRANSFORM = "transform"
INTERACTIVE_MODE_DYNAMIC_TRANSFORM = "dynamic_transform"


class ViewController(QtCore.QObject):
    def app_init(self, rpa_app):
        self.__rpa = rpa_app.rpa
        self.__main_window = rpa_app.main_window
        self.__cmd_line_args = rpa_app.cmd_line_args

        self.__viewport_api = self.__rpa.viewport_api
        self.__session_api = self.__rpa.session_api
        self.__color_api = self.__rpa.color_api

        self.__mousewheel_mins = [0, 0]

        self.__core_view = self.__main_window.get_core_view()
        self.__core_view.installEventFilter(self)

        self.__current_rotation_val = self.__viewport_api.get_rotation()
        self.__image_rot_slider = None
        self.__create_tool_bar()

        self.__actions = Actions()
        self.__connect_signals()
        self.__create_menu_bar()

        self.__panning_in_progress = False
        self.__interactive_mode = self.__rpa.session_api.get_custom_session_attr(INTERACTIVE_MODE)
        dm = self.__session_api.delegate_mngr
        dm.add_post_delegate(self.__session_api.set_custom_session_attr, self.__update_interactive_mode)

        self.__actions.reset_viewer.setProperty("hotkey_editor", True)
        self.__actions.fullscreen.setProperty("hotkey_editor", True)
        self.__actions.fit_to_window.setProperty("hotkey_editor", True)
        self.__actions.fit_to_width.setProperty("hotkey_editor", True)
        self.__actions.fit_to_height.setProperty("hotkey_editor", True)
        self.__actions.zoom_in.setProperty("hotkey_editor", True)
        self.__actions.zoom_out.setProperty("hotkey_editor", True)
        self.__actions.flip_x.setProperty("hotkey_editor", True)
        self.__actions.flip_y.setProperty("hotkey_editor", True)
        self.__actions.toggle_presentation_mode.setProperty("hotkey_editor", True)

        dm = self.__viewport_api.delegate_mngr
        dm.add_post_delegate(self.__viewport_api.flip_x, self.__flip_x)
        dm.add_post_delegate(self.__viewport_api.flip_y, self.__flip_y)
        dm.add_post_delegate(self.__viewport_api.set_rotation, self.__post_set_rotation)

    def __connect_signals(self):
        self.__actions.fullscreen.triggered.connect(lambda state:
                                                    self.toggle_fullscreen(state))
        self.__actions.fit_to_window.triggered.connect(lambda state:
                                                       self.__viewport_api.fit_to_window(state))
        self.__actions.fit_to_width.triggered.connect(lambda state:
                                                       self.__viewport_api.fit_to_width(state))
        self.__actions.fit_to_height.triggered.connect(lambda state:
                                                       self.__viewport_api.fit_to_height(state))

        self.__actions.zoom_in.triggered.connect(lambda:
                                                 self.__zoom_in())
        self.__actions.zoom_out.triggered.connect(lambda:
                                                  self.__zoom_out())
        self.__actions.flip_x.triggered.connect(lambda state:
                                                self.__viewport_api.flip_x(state))
        self.__actions.flip_y.triggered.connect(lambda state:
                                                self.__viewport_api.flip_y(state))
        self.__actions.reset_viewer.triggered.connect(self.__reset_viewer)

        self.__actions.toggle_presentation_mode.triggered.connect(
            self.__toggle_presentation_mode)

        def __set_zoom_mode(mode):
            return lambda: self.__viewport_api.set_scale(float(mode))

        for mode, action in self.__actions.zoom_modes.items():
            action.triggered.connect(__set_zoom_mode(mode))

        # Image Rotation
        self.__actions.rotation_reset.triggered.connect(lambda: self.__update_rotation(0))
        self.__actions.rotate_90.triggered.connect(lambda: self.__update_rotation(90))
        self.__actions.rotate_180.triggered.connect(lambda: self.__update_rotation(180))
        self.__actions.rotate_270.triggered.connect(lambda: self.__update_rotation(270))
        self.__actions.rotate_up_10.triggered.connect(lambda: self.__update_rotation(self.__current_rotation_val + 10))
        self.__actions.rotate_down_10.triggered.connect(lambda: self.__update_rotation(self.__current_rotation_val - 10))
        self.__actions.rotation_slider.triggered.connect(lambda state:self.__toggle_image_rot_slider(state))
        self.__image_rot_slider.SIG_SLIDER_VALUE_CHANGED.connect(self.set_image_rot_value)
        self.__image_rot_slider.SIG_RESET.connect(lambda: self.__update_rotation(0))
        self.__image_rot_slider.SIG_TOOLBAR_VISIBLE.connect(self.__set_image_rot_visibility)

    def __create_menu_bar(self):
        view_menu = self.__main_window.get_menu("View")
        view_menu.addAction(self.__actions.toggle_presentation_mode)
        view_menu.addSeparator()
        view_menu.addAction(self.__actions.reset_viewer)
        view_menu.addAction(self.__actions.fullscreen)
        fit_to_actions = [self.__actions.fit_to_window,
                          self.__actions.fit_to_width,
                          self.__actions.fit_to_height]
        for action in fit_to_actions:
            view_menu.addAction(action)
        view_menu.addSeparator()
        view_menu.addAction(self.__actions.flip_x)
        view_menu.addAction(self.__actions.flip_y)
        view_menu.addSeparator()
        image_rot_menu = view_menu.addMenu("Image Rotation")
        image_rot_menu.addAction(self.__actions.rotation_reset)
        image_rot_menu.addAction(self.__actions.rotate_90)
        image_rot_menu.addAction(self.__actions.rotate_180)
        image_rot_menu.addAction(self.__actions.rotate_270)
        image_rot_menu.addSeparator()
        image_rot_menu.addAction(self.__actions.rotate_up_10)
        image_rot_menu.addAction(self.__actions.rotate_down_10)
        image_rot_menu.addSeparator()
        image_rot_menu.addAction(self.__actions.rotation_slider)
        view_menu.addMenu(image_rot_menu)
        view_menu.addSeparator()
        view_menu.addAction(self.__actions.zoom_in)
        view_menu.addAction(self.__actions.zoom_out)
        view_menu.addSeparator()

        zoom_modes = view_menu.addMenu("Zoom Modes")
        for action in self.__actions.zoom_modes.values():
            zoom_modes.addAction(action)
        view_menu.addSeparator()

    def __create_tool_bar(self):
        self.__image_rot_slider = SliderToolBar(
                                    "Image Rotation", "Rotation",
                                    min_val=-360,
                                    max_val=360,
                                    value=0,
                                    interval=90)
        self.__main_window.addToolBar(
                QtCore.Qt.BottomToolBarArea, self.__image_rot_slider)
        self.__image_rot_slider.set_slider_value(self.__current_rotation_val)

    def __reset_viewer(self):
        self.__color_api.set_fstop(0.0)
        self.__color_api.set_gamma(1.0)
        # Reset to Color(RGB)
        self.__color_api.set_channel(4)

        self.__actions.flip_x.setChecked(False)
        self.__actions.flip_y.setChecked(False)

        fit_mode = self.__actions.fit_modes_radio.checkedAction()
        if fit_mode is None:
            self.__viewport_api.set_scale(1)
            self.__viewport_api.set_translation(0, 0)
        else:
            fit_mode.setChecked(False)
            fit_mode.trigger()
        self.__viewport_api.display_msg("Viewer is reset")

    def __zoom_in(self):
        current_zoom = self.__viewport_api.get_scale()
        new_zoom = _round_up_pow2(current_zoom[0])
        self.__viewport_api.set_scale(new_zoom)

    def __zoom_out(self):
        current_zoom = self.__viewport_api.get_scale()
        new_zoom = _round_down_pow2(current_zoom[0])
        self.__viewport_api.set_scale(new_zoom)

    def __update_interactive_mode(self, out, attr_id, value):
        if attr_id == INTERACTIVE_MODE:
            self.__interactive_mode = value

    def toggle_fullscreen(self, state):
        self.__main_window.toggle_fullscreen()

    def eventFilter(self, obj, event):
        if not (
                event.type() == QtCore.QEvent.MouseButtonPress or \
                event.type() == QtCore.QEvent.MouseMove or \
                event.type() == QtCore.QEvent.MouseButtonRelease or \
                event.type() == QtCore.QEvent.Wheel):
            return False

        get_pos = lambda: (event.pos().x(), obj.height() - event.pos().y())

        if self.__interactive_mode in \
                    (INTERACTIVE_MODE_MOVE,
                     INTERACTIVE_MODE_DYNAMIC_TRANSFORM,
                     INTERACTIVE_MODE_TRANSFORM):
            return False

        if event.type() == QtCore.QEvent.Wheel:
            self.__geometry = self.__viewport_api.get_current_clip_geometry()

            zoom_point = get_pos()
            delta = event.delta()
            speed = 2.0  # multiple values for different zoom types (keyboard, mouse, gesture)

            if delta > 0:
                if self.__mousewheel_mins[0] == 0:
                    self.__mousewheel_mins[0] = delta
                elif self.__mousewheel_mins[0] > delta:
                    self.__mousewheel_mins[0] = delta
                delta = delta / self.__mousewheel_mins[0]
            elif delta < 0:
                if self.__mousewheel_mins[1] == 0:
                    self.__mousewheel_mins[1] = delta
                elif self.__mousewheel_mins[1] < delta:
                    self.__mousewheel_mins[1] = delta
                delta = -delta / self.__mousewheel_mins[1]

            self.__vertical_lock = False
            self.__horizontal_lock = False
            self.__viewport_api.scale_on_point(
                zoom_point, delta, speed,
                self.__horizontal_lock, self.__vertical_lock)

        if event.type() == QtCore.QEvent.MouseButtonPress:
            if event.button() == QtCore.Qt.MiddleButton and event.modifiers() == QtCore.Qt.NoModifier:
                self.__panning_in_progress = True
                self.__viewport_api.start_drag(get_pos())
        if self.__panning_in_progress and event.type() == QtCore.QEvent.MouseMove:
            self.__viewport_api.drag(get_pos())
        if event.type() == QtCore.QEvent.MouseButtonRelease:
            if event.button() == QtCore.Qt.MiddleButton and event.modifiers() == QtCore.Qt.NoModifier:
                self.__panning_in_progress = False
                self.__viewport_api.end_drag()

        return False

    def __toggle_presentation_mode(self):
        self.__viewport_api.toggle_presentation_mode()

    def post_app_init(self):
        pass
        # if self.__cmd_line_args.fullscreen:
        #     self.__actions.fullscreen.setChecked(True)
        #     self.toggle_fullscreen(True)

    #     if self.__cmd_line_args.zoom is not None:
    #         scale = float(self.__cmd_line_args.zoom[0])
    #         self.__viewport_api.set_scale(scale)

        if self.__cmd_line_args.rotate is not None:
            deg = float(self.__cmd_line_args.rotate[0])
            self.set_image_rot_value(deg)

    def add_cmd_line_args(self, parser):
        group = parser.add_argument_group("View Controls")
        group.add_argument(
            '--fs', '--fullscreen',
            action='store_true',
            dest='fullscreen',
            help='Start up in Fullscreen mode'
        )
        group.add_argument(
            '--z', '--zoom',
            action='store',
            metavar='SCALE',
            type=float,
            nargs=1,
            dest='zoom',
            help='Zoom in/out viewport to a factor of SCALE'
        )
        group.add_argument(
            '--rot', '--rotate',
            action='store',
            metavar='DEGREE',
            type=float,
            nargs=1,
            dest='rotate',
            help='Rotate images to DEGREE'
        )

    def __flip_x(self, out, state):
        self.__actions.flip_x.setChecked(state)

    def __flip_y(self, out, state):
        self.__actions.flip_y.setChecked(state)

    # Image rotation
    def __set_image_rot_visibility(self):
        is_visible = self.__image_rot_slider.isVisible()
        self.__actions.rotation_slider.setChecked(is_visible)
        self.__toggle_image_rot_slider(is_visible)

    def __toggle_image_rot_slider(self, state):
        if state:
            self.__image_rot_slider.show()
        else:
            self.__image_rot_slider.hide()

    def set_image_rot_value(self, angle):
        if angle is None: return
        self.__viewport_api.set_rotation(angle)

    def __update_rotation(self, angle):
        self.__viewport_api.set_rotation(angle)

    def __post_set_rotation(self, out, angle):
        self.__current_rotation_val = angle
        self.__image_rot_slider.set_slider_value(angle)
        self.__viewport_api.display_msg("Rotation: %d" % angle)
