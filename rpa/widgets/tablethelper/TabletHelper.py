"""
TabletHelper Widget - Pure UI toolbar widget for tablet-based review workflows.

This widget provides a toolbar with buttons and controls for annotation,
playback, and display features. All action slots are placeholders for
future implementation.
"""

import rpa.widgets.tablethelper.resources.resources

# PySide import fallback: Try PySide2 first, then PySide6
try:
    # PySide2 (Qt5): QAction, QPushButton, QSlider, QWidgetAction are in QtWidgets
    from PySide2.QtCore import Qt, QSize, QTimer, Signal, Slot
    from PySide2.QtGui import QColor, QIcon, QPalette
    from PySide2.QtWidgets import (
        QAction, QMenu, QPushButton, QSlider, QToolBar, QToolButton, QWidgetAction
    )
    PYSIDE_VERSION = 2
except ImportError:
    try:
        # PySide6 (Qt6): QAction moved to QtGui, QPushButton, QSlider, QWidgetAction still in QtWidgets
        from PySide6.QtCore import Qt, QSize, QTimer, Signal, Slot
        from PySide6.QtGui import QAction, QColor, QIcon, QPalette
        from PySide6.QtWidgets import (
            QMenu, QPushButton, QSlider, QToolBar, QToolButton, QWidgetAction
        )
        PYSIDE_VERSION = 6
    except ImportError:
        raise ImportError(
            "Neither PySide2 nor PySide6 is available. "
            "Please install one of them."
        )


# Constants
# Default values for sliders
DEFAULT_MAX_PEN_WIDTH = 100
DEFAULT_MAX_ERASER_WIDTH = 100
DEFAULT_PEN_WIDTH = 30
DEFAULT_ERASER_WIDTH = 30
DEFAULT_CONTRAST_MAX = 80
DEFAULT_CONTRAST_MIN = 0

# Toggle color for active buttons
TOGGLE_ON_COLOR = (0.63, 0.63, 0.63)


def _load_icon(icon_filename):
    """
    Load an icon from Qt resources.

    Since the resources module is imported, icons are accessed directly
    from the compiled Qt resource system using the :icon_filename format.

    Args:
        icon_filename: Name of the icon file (e.g., "applications-graphics.png")

    Returns:
        QIcon: The loaded icon from Qt resources
    """
    # Load from Qt resources using the : prefix format
    # The resources module must be imported for this to work
    resource_path = f":{icon_filename}"
    icon = QIcon(resource_path)

    # Warn if icon is not found (should not happen if resources are properly compiled)
    if icon.isNull() or not icon.availableSizes():
        print(f"[TabletHelper] WARNING: Icon not found in resources: {icon_filename}")

    return icon


class SliderWidgetAction(QWidgetAction):
    """
    Custom widget action that creates a slider widget.

    This class wraps a QSlider in a QWidgetAction to be used in menus
    and toolbars.
    """

    def __init__(self, parent, orientation=Qt.Vertical,
                 minimum=None, maximum=None, tick_interval=None,
                 single_step=None, maximum_width=None):
        """
        Initialize the slider widget action.

        Args:
            parent: Parent widget
            orientation: Slider orientation (Qt.Vertical or Qt.Horizontal)
            minimum: Minimum slider value
            maximum: Maximum slider value
            tick_interval: Interval between tick marks
            single_step: Single step increment
            maximum_width: Maximum width of the slider
        """
        super().__init__(parent)

        self._orientation = orientation
        self._minimum = minimum
        self._maximum = maximum
        self._tick_interval = tick_interval
        self._single_step = single_step
        self._maximum_width = maximum_width

    def createWidget(self, parent):
        """
        Create the slider widget.

        Args:
            parent: Parent widget for the slider

        Returns:
            QSlider: Configured slider widget
        """
        slider = QSlider(self._orientation, parent)
        if self._minimum is not None:
            slider.setMinimum(self._minimum)
        if self._maximum is not None:
            slider.setMaximum(self._maximum)
        if self._tick_interval is not None:
            slider.setTickInterval(self._tick_interval)
        if self._single_step is not None:
            slider.setSingleStep(self._single_step)
        if self._maximum_width is not None:
            slider.setMaximumWidth(self._maximum_width)
        return slider

    def getCreatedWidget(self):
        """
        Get the created slider widget.

        Returns:
            QSlider: The slider widget instance

        Raises:
            AssertionError: If no widget or multiple widgets exist
        """
        widgets = self.createdWidgets()
        assert widgets, "No widgets created"
        assert len(widgets) == 1, "Multiple widgets created"
        return widgets[0]


class TabletHelper(QToolBar):
    """
    Tablet Helper Widget - Pure UI toolbar for tablet-based review workflows.

    This widget provides a toolbar with buttons for various annotation,
    playback, and display controls. All action slots are placeholders
    for future implementation.
    """

    # Signals for future implementation
    color_cycled = Signal()
    annotations_cleared = Signal()
    annotation_undo = Signal()
    annotation_redo = Signal()
    audio_muted = Signal(bool)
    next_clip = Signal()
    prev_clip = Signal()
    next_annotation = Signal()
    prev_annotation = Signal()
    lights_dimmed = Signal(bool)
    audio_waveform_toggled = Signal(bool)
    color_swatch_selected = Signal(tuple)  # (r, g, b)
    photo_plugin_toggled = Signal(bool)
    frame_overlay_toggled = Signal(bool)
    text_overlay_toggled = Signal(bool)
    all_overlays_toggled = Signal(bool)
    audio_scrub_toggled = Signal(bool)
    mask_toggled = Signal(bool)
    pen_tool_selected = Signal(bool)
    eraser_tool_selected = Signal(bool)
    color_picker_selected = Signal()
    orientation_changed = Signal(int)  # Qt.Horizontal or Qt.Vertical
    pen_width_changed = Signal(int)
    eraser_width_changed = Signal(int)
    contrast_changed = Signal(float)

    def __init__(self, rpa, parent=None):
        """
        Initialize the TabletHelper widget.

        Args:
            rpa: RPA instance
            parent: Parent widget (optional)
        """
        super().__init__("Tablet Helper", parent)
        self.setObjectName("TabletHelper")

        self.__rpa = rpa
        self._orient_horizontal = False
        self._default_color = None
        self._mode_actions = []
        self._current_mode_action = None  # Track currently active mode action

        # Slider widgets
        self._pen_width_slider = None
        self._erase_width_slider = None
        self._contrast_slider = None

        # Slider widget actions (needed to access widgets when menus are shown)
        self._pen_width_swa = None
        self._erase_width_swa = None
        self._contrast_swa = None

        # Actions
        self.color_action = None
        self.clear_anno_action = None
        self.undo_anno_action = None
        self.redo_anno_action = None
        self.mute_action = None
        self.next_clip_action = None
        self.prev_clip_action = None
        self.next_anno_action = None
        self.prev_anno_action = None
        # self.dim_action = None
        # self.audio_wf_action = None
        self.color_swatch_action = None
        self.photo_action = None
        self.frame_action = None
        self.text_action = None
        self.overlay_action = None
        self.scrub_action = None
        self.mask_action = None
        self.pen_action = None
        self.eraser_action = None
        self.color_pick_action = None
        self.orient_action = None
        # self.contrast_action = None
        self.pen_size_action = None
        self.eraser_size_action = None

        self._init_actions()
        self._init_toolbar()

    def _init_actions(self):
        """Initialize all toolbar actions with icons and tooltips."""
        # Color and annotation actions
        self.color_action = QAction(
            _load_icon("applications-graphics.png"),
            "Cycle Annotation Color",
            self
        )
        self.clear_anno_action = QAction(
            _load_icon("edit-clear.png"),
            "Clear Annotations",
            self
        )
        self.undo_anno_action = QAction(
            _load_icon("edit-undo.png"),
            "Undo Annotation",
            self
        )
        self.redo_anno_action = QAction(
            _load_icon("edit-redo.png"),
            "Redo Annotation",
            self
        )

        # Playback actions
        self.mute_action = QAction(
            _load_icon("audio-volume-muted.png"),
            "Mute Audio",
            self
        )
        self.next_clip_action = QAction(
            _load_icon("go-next.png"),
            "Next Clip",
            self
        )
        self.prev_clip_action = QAction(
            _load_icon("go-previous.png"),
            "Previous Clip",
            self
        )

        # Annotation navigation
        self.next_anno_action = QAction(
            _load_icon("arrow-right-double.png"),
            "Next Annotation",
            self
        )
        self.prev_anno_action = QAction(
            _load_icon("arrow-left-double.png"),
            "Previous Annotation",
            self
        )

        # Display and tool actions
        # self.dim_action = QAction(
        #     _load_icon("help-hint.png"),
        #     "Dim Lights",
        #     self
        # )
        # self.audio_wf_action = QAction(
        #     _load_icon("applications-multimedia.png"),
        #     "Audio Waveforms",
        #     self
        # )
        self.color_swatch_action = QAction(
            _load_icon("fill-color.png"),
            "Color Swatch",
            self
        )
        self.photo_action = QAction(
            _load_icon("preferences-desktop-user.png"),
            "Photo Plugin",
            self
        )
        self.frame_action = QAction(
            _load_icon("frame-overlay.png"),
            "Display frame overlay",
            self
        )
        self.text_action = QAction(
            _load_icon("text-overlay.png"),
            "Display text overlay",
            self
        )
        self.overlay_action = QAction(
            _load_icon("all-overlay.png"),
            "Display all overlays",
            self
        )
        self.scrub_action = QAction(
            _load_icon("applications-media-scrub.png"),
            "Play audio while scrubbing",
            self
        )
        self.mask_action = QAction(
            _load_icon("insert-image.png"),
            "Toggle Mask",
            self
        )

        # Drawing tools
        self.pen_action = QAction(
            _load_icon("draw-freehand.png"),
            "Pen Tool",
            self
        )
        self.eraser_action = QAction(
            _load_icon("draw-eraser.png"),
            "Eraser Tool",
            self
        )
        self.color_pick_action = QAction(
            _load_icon("color-picker.png"),
            "Color Picker",
            self
        )

        # Toolbar control
        self.orient_action = QAction(
            _load_icon("orient-horizontal.png"),
            "Change Toolbar Orientation",
            self
        )

        # Create slider widgets
        self._create_pen_size_slider()
        self._create_eraser_slider()
        self._create_contrast_slider()

        # Connect actions to placeholder slots
        self.color_action.triggered.connect(self._on_cycle_color)
        self.clear_anno_action.triggered.connect(self._on_clear_annotations)
        self.undo_anno_action.triggered.connect(self._on_undo_annotation)
        self.redo_anno_action.triggered.connect(self._on_redo_annotation)
        self.mute_action.triggered.connect(self._on_mute_audio)
        self.next_clip_action.triggered.connect(self._on_next_clip)
        self.prev_clip_action.triggered.connect(self._on_prev_clip)
        self.next_anno_action.triggered.connect(self._on_next_annotation)
        self.prev_anno_action.triggered.connect(self._on_prev_annotation)
        # self.dim_action.triggered.connect(self._on_dim_lights)
        # self.audio_wf_action.triggered.connect(self._on_audio_waveform)
        self.color_swatch_action.triggered.connect(self._on_color_swatch)
        self.photo_action.triggered.connect(self._on_photo_plugin)
        self.frame_action.triggered.connect(self._on_frame_overlay)
        self.text_action.triggered.connect(self._on_text_overlay)
        self.overlay_action.triggered.connect(self._on_all_overlays)
        self.scrub_action.triggered.connect(self._on_audio_scrub)
        self.mask_action.triggered.connect(self._on_toggle_mask)
        self.pen_action.triggered.connect(self._on_pen_select)
        self.eraser_action.triggered.connect(self._on_eraser_select)
        self.color_pick_action.triggered.connect(self._on_color_picker)
        self.orient_action.triggered.connect(self._on_orientation_change)

        # Track mode actions for visual feedback
        self._mode_actions.extend([self.pen_action, self.eraser_action])

    def _init_toolbar(self):
        """Initialize the toolbar with all actions."""
        # Add actions to toolbar in order
        self.addAction(self.orient_action)
        # self.addAction(self.dim_action)
        # self.addWidget(self.contrast_action)
        self.addAction(self.color_action)
        self.addAction(self.color_pick_action)
        self.addAction(self.pen_action)
        self.addWidget(self.pen_size_action)
        self.addAction(self.eraser_action)
        self.addWidget(self.eraser_size_action)
        self.addAction(self.clear_anno_action)
        self.addAction(self.undo_anno_action)
        self.addAction(self.redo_anno_action)
        self.addAction(self.prev_anno_action)
        self.addAction(self.next_anno_action)
        self.addAction(self.prev_clip_action)
        self.addAction(self.next_clip_action)
        self.addAction(self.mute_action)
        self.addAction(self.scrub_action)
        self.addAction(self.mask_action)
        # self.addAction(self.audio_wf_action)
        self.addAction(self.color_swatch_action)
        self.addAction(self.photo_action)
        self.addAction(self.frame_action)
        self.addAction(self.text_action)
        self.addAction(self.overlay_action)

        # Set toolbar window flags
        self.setWindowFlags(
            Qt.Tool | Qt.WindowStaysOnTopHint |
            Qt.FramelessWindowHint | Qt.X11BypassWindowManagerHint
        )
        # Ensure toolbar is movable - this enables the native drag handle
        # For floating toolbars, Qt automatically shows a handle area at the start
        self.setMovable(True)

        # Set auto-fill background for toggle buttons
        toggle_actions = [
            self.photo_action, self.scrub_action, self.mask_action,
            self.text_action, self.color_action,
            self.pen_action, self.eraser_action, self.frame_action
        ]
        for action in toggle_actions:
            widget = self.widgetForAction(action)
            if widget:
                widget.setAutoFillBackground(True)

        # Match reference toolbar icon size for compact appearance
        self.setIconSize(QSize(16, 16))

        # Reduce toolbar spacing for more compact layout (match reference)
        layout = self.layout()
        if layout:
            layout.setSpacing(0)
            layout.setContentsMargins(0, 0, 0, 0)

        # Set tool button style to show icons only for all actions
        for action in self.actions():
            widget = self.widgetForAction(action)
            if widget and isinstance(widget, QToolButton):
                widget.setToolButtonStyle(Qt.ToolButtonIconOnly)
                widget.setFocusPolicy(Qt.NoFocus)
                # Reduce button padding for more compact appearance
                widget.setStyleSheet("QToolButton { padding: 2px; }")

        # Get default background color
        frame_widget = self.widgetForAction(self.frame_action)
        if frame_widget:
            palette = frame_widget.palette().color(frame_widget.backgroundRole())
            self._default_color = (
                palette.red() / 255.0,
                palette.green() / 255.0,
                palette.blue() / 255.0
            )

        # Initialize orientation state to match actual toolbar orientation
        self._orient_horizontal = (self.orientation() == Qt.Horizontal)
        self._update_orientation_icon()

    def _create_pen_size_slider(self):
        """Create the pen size slider widget."""
        pen_size_menu = QMenu('')
        self._pen_width_swa = SliderWidgetAction(
            pen_size_menu,
            orientation=Qt.Vertical,
            minimum=1,
            maximum=DEFAULT_MAX_PEN_WIDTH,
            maximum_width=20
        )
        pen_size_menu.addAction(self._pen_width_swa)

        # Connect to menu's aboutToShow signal to get slider widget when it's created
        def _on_pen_menu_about_to_show():
            # Use QTimer to ensure widget is created after menu is shown
            def _get_slider_widget():
                if self._pen_width_slider is None:
                    widgets = self._pen_width_swa.createdWidgets()
                    if widgets:
                        self._pen_width_slider = widgets[0]
                        # Set default value to DEFAULT_PEN_WIDTH
                        self._pen_width_slider.setValue(DEFAULT_PEN_WIDTH)
                        self._pen_width_slider.valueChanged.connect(self._on_pen_width_changed)
                        pen_size_menu.setMinimumWidth(self._pen_width_slider.width() + 6)
                        # Update icon based on default slider value (without selecting tool)
                        icon_index = self._calculate_icon_index(DEFAULT_PEN_WIDTH, DEFAULT_MAX_PEN_WIDTH)
                        icon_path = f"brush_{icon_index}.png"
                        self.pen_size_action.setIcon(_load_icon(icon_path))

            QTimer.singleShot(0, _get_slider_widget)

        pen_size_menu.aboutToShow.connect(_on_pen_menu_about_to_show)

        # Calculate default icon index for width 30
        default_icon_index = self._calculate_icon_index(DEFAULT_PEN_WIDTH, DEFAULT_MAX_PEN_WIDTH)
        default_icon_path = f"brush_{default_icon_index}.png"

        self.pen_size_action = QToolButton(self)
        self.pen_size_action.setToolTip("Pen Size")
        self.pen_size_action.setMenu(pen_size_menu)
        self.pen_size_action.setPopupMode(QToolButton.InstantPopup)
        self.pen_size_action.setIcon(_load_icon(default_icon_path))
        self.pen_size_action.setToolButtonStyle(Qt.ToolButtonIconOnly)
        self.pen_size_action.setFocusPolicy(Qt.NoFocus)

    def _create_eraser_slider(self):
        """Create the eraser size slider widget."""
        eraser_size_menu = QMenu('')
        self._erase_width_swa = SliderWidgetAction(
            eraser_size_menu,
            orientation=Qt.Vertical,
            minimum=1,
            maximum=DEFAULT_MAX_ERASER_WIDTH,
            maximum_width=20
        )
        eraser_size_menu.addAction(self._erase_width_swa)

        # Connect to menu's aboutToShow signal to get slider widget when it's created
        def _on_eraser_menu_about_to_show():
            # Use QTimer to ensure widget is created after menu is shown
            def _get_slider_widget():
                if self._erase_width_slider is None:
                    widgets = self._erase_width_swa.createdWidgets()
                    if widgets:
                        self._erase_width_slider = widgets[0]
                        # Set default value to DEFAULT_ERASER_WIDTH
                        self._erase_width_slider.setValue(DEFAULT_ERASER_WIDTH)
                        self._erase_width_slider.valueChanged.connect(
                            self._on_eraser_width_changed
                        )
                        eraser_size_menu.setMinimumWidth(
                            self._erase_width_slider.width() + 6
                        )
                        # Update icon based on default slider value (without selecting tool)
                        icon_index = self._calculate_icon_index(DEFAULT_ERASER_WIDTH, DEFAULT_MAX_ERASER_WIDTH)
                        icon_path = f"eraser_{icon_index}.png"
                        self.eraser_size_action.setIcon(_load_icon(icon_path))

            QTimer.singleShot(0, _get_slider_widget)

        eraser_size_menu.aboutToShow.connect(_on_eraser_menu_about_to_show)

        # Calculate default icon index for width 30
        default_icon_index = self._calculate_icon_index(DEFAULT_ERASER_WIDTH, DEFAULT_MAX_ERASER_WIDTH)
        default_icon_path = f"eraser_{default_icon_index}.png"

        self.eraser_size_action = QToolButton(self)
        self.eraser_size_action.setToolTip("Eraser Size")
        self.eraser_size_action.setMenu(eraser_size_menu)
        self.eraser_size_action.setPopupMode(QToolButton.InstantPopup)
        self.eraser_size_action.setIcon(_load_icon(default_icon_path))
        self.eraser_size_action.setToolButtonStyle(Qt.ToolButtonIconOnly)
        self.eraser_size_action.setFocusPolicy(Qt.NoFocus)

    def _create_contrast_slider(self):
        """Create the contrast slider widget."""
        contrast_menu = QMenu('')
        self._contrast_swa = SliderWidgetAction(
            contrast_menu,
            orientation=Qt.Vertical,
            minimum=DEFAULT_CONTRAST_MIN,
            maximum=DEFAULT_CONTRAST_MAX,
            maximum_width=20
        )
        contrast_menu.addAction(self._contrast_swa)

        # Connect to menu's aboutToShow signal to get slider widget when it's created
        def _on_contrast_menu_about_to_show():
            # Use QTimer to ensure widget is created after menu is shown
            def _get_slider_widget():
                if self._contrast_slider is None:
                    widgets = self._contrast_swa.createdWidgets()
                    if widgets:
                        self._contrast_slider = widgets[0]
                        self._contrast_slider.valueChanged.connect(self._on_contrast_changed)
                        contrast_menu.setMinimumWidth(self._contrast_slider.width() + 6)

            QTimer.singleShot(0, _get_slider_widget)

        contrast_menu.aboutToShow.connect(_on_contrast_menu_about_to_show)

        # self.contrast_action = QToolButton(self)
        # self.contrast_action.setToolTip("Contrast (Not Available)")
        # self.contrast_action.setMenu(contrast_menu)
        # self.contrast_action.setPopupMode(QToolButton.InstantPopup)
        # self.contrast_action.setIcon(_load_icon("contrast.png"))
        # self.contrast_action.setToolButtonStyle(Qt.ToolButtonIconOnly)
        # self.contrast_action.setFocusPolicy(Qt.NoFocus)
        # self.contrast_action.setEnabled(False)

    def set_visible(self, visible):
        """
        Set the visibility of the toolbar.

        Args:
            visible: True to show the toolbar, False to hide it
        """
        if visible:
            self.show()
        else:
            self.hide()

    def set_orientation(self, orientation):
        """
        Set the toolbar orientation.

        Args:
            orientation: Qt.Horizontal or Qt.Vertical
        """
        self.hide()
        self.setOrientation(orientation)
        self._orient_horizontal = (orientation == Qt.Horizontal)
        self._update_orientation_icon()
        self.show()

    def _update_orientation_icon(self):
        """Update the orientation icon based on current orientation."""
        if not self.orient_action:
            return

        if self.orientation() == Qt.Horizontal:
            self.orient_action.setIcon(
                _load_icon("orient-vertical.png")
            )
        else:
            self.orient_action.setIcon(
                _load_icon("orient-horizontal.png")
            )

    def _set_interactive_mode_visual(self, current_action):
        """
        Update visual feedback for mode actions.

        Args:
            current_action: The currently active action, or None
        """
        self._current_mode_action = current_action
        for action in self._mode_actions:
            widget = self.widgetForAction(action)
            if widget:
                if action is current_action:
                    qcolor = QColor(*[
                        int(x * 255) for x in TOGGLE_ON_COLOR
                    ])
                else:
                    qcolor = QColor(*[
                        int(x * 255) for x in self._default_color
                    ])
                palette = widget.palette()
                palette.setColor(widget.backgroundRole(), qcolor)
                widget.setPalette(palette)

    def _calculate_icon_index(self, width, max_width):
        """
        Calculate icon index from width value.

        Args:
            width: Current width value
            max_width: Maximum width value

        Returns:
            int: Icon index (0-9)
        """
        # Calculate index: (width-1)/(max_width/10)
        # This maps width values to icon indices 0-9
        index = int((width - 1) / (max_width / 10))
        # Clamp to valid range
        return max(0, min(9, index))

    # Placeholder slots for actions

    @Slot()
    def _on_cycle_color(self):
        """Placeholder slot for cycle color action."""
        print("[TabletHelper] DEBUG: Cycle Color action triggered")
        self.color_cycled.emit()

    @Slot()
    def _on_clear_annotations(self):
        """Placeholder slot for clear annotations action."""
        print("[TabletHelper] DEBUG: Clear Annotations action triggered")
        self.annotations_cleared.emit()

    @Slot()
    def _on_undo_annotation(self):
        """Placeholder slot for undo annotation action."""
        print("[TabletHelper] DEBUG: Undo Annotation action triggered")
        self.annotation_undo.emit()

    @Slot()
    def _on_redo_annotation(self):
        """Placeholder slot for redo annotation action."""
        print("[TabletHelper] DEBUG: Redo Annotation action triggered")
        self.annotation_redo.emit()

    @Slot()
    def _on_mute_audio(self):
        """Placeholder slot for mute audio action."""
        print("[TabletHelper] DEBUG: Mute Audio action triggered")
        # Toggle state would be managed by external logic
        self.audio_muted.emit(True)

    @Slot()
    def _on_next_clip(self):
        """Placeholder slot for next clip action."""
        print("[TabletHelper] DEBUG: Next Clip action triggered")
        self.next_clip.emit()

    @Slot()
    def _on_prev_clip(self):
        """Placeholder slot for previous clip action."""
        print("[TabletHelper] DEBUG: Previous Clip action triggered")
        self.prev_clip.emit()

    @Slot()
    def _on_next_annotation(self):
        """Placeholder slot for next annotation action."""
        print("[TabletHelper] DEBUG: Next Annotation action triggered")
        self.next_annotation.emit()

    @Slot()
    def _on_prev_annotation(self):
        """Placeholder slot for previous annotation action."""
        print("[TabletHelper] DEBUG: Previous Annotation action triggered")
        self.prev_annotation.emit()

    # @Slot()
    # def _on_dim_lights(self):
    #     """Placeholder slot for dim lights action."""
    #     print("[TabletHelper] DEBUG: Dim Lights action triggered")
    #     # Toggle state would be managed by external logic
    #     self.lights_dimmed.emit(True)

    # @Slot()
    # def _on_audio_waveform(self):
    #     """Placeholder slot for audio waveform action."""
    #     print("[TabletHelper] DEBUG: Audio Waveform action triggered")
    #     # Toggle state would be managed by external logic
    #     self.audio_waveform_toggled.emit(True)

    @Slot()
    def _on_color_swatch(self):
        """Placeholder slot for color swatch action."""
        print("[TabletHelper] DEBUG: Color Swatch action triggered")
        # Color selection would be handled by external logic
        self.color_swatch_selected.emit((1.0, 1.0, 1.0))

    @Slot()
    def _on_photo_plugin(self):
        """Placeholder slot for photo plugin action."""
        print("[TabletHelper] DEBUG: Photo Plugin action triggered")
        # Toggle state would be managed by external logic
        self.photo_plugin_toggled.emit(True)

    @Slot()
    def _on_frame_overlay(self):
        """Placeholder slot for frame overlay action."""
        print("[TabletHelper] DEBUG: Frame Overlay action triggered")
        # Toggle state would be managed by external logic
        self.frame_overlay_toggled.emit(True)

    @Slot()
    def _on_text_overlay(self):
        """Placeholder slot for text overlay action."""
        print("[TabletHelper] DEBUG: Text Overlay action triggered")
        # Toggle state would be managed by external logic
        self.text_overlay_toggled.emit(True)

    @Slot()
    def _on_all_overlays(self):
        """Placeholder slot for all overlays action."""
        print("[TabletHelper] DEBUG: All Overlays action triggered")
        self.all_overlays_toggled.emit(True)

    @Slot()
    def _on_audio_scrub(self):
        """Placeholder slot for audio scrub action."""
        print("[TabletHelper] DEBUG: Audio Scrub action triggered")
        # Toggle state would be managed by external logic
        self.audio_scrub_toggled.emit(True)

    @Slot()
    def _on_toggle_mask(self):
        """Placeholder slot for toggle mask action."""
        print("[TabletHelper] DEBUG: Toggle Mask action triggered")
        # Toggle state would be managed by external logic
        self.mask_toggled.emit(True)

    @Slot()
    def _on_pen_select(self):
        """
        Handle pen tool selection with toggle behavior.

        If pen is already selected, deselects it. Otherwise, selects pen
        and deselects eraser (mutual exclusivity).
        """
        # Toggle: if pen is already active, deselect it
        if self._current_mode_action is self.pen_action:
            self._set_interactive_mode_visual(None)
            self.pen_tool_selected.emit(False)
        else:
            # Select pen and deselect eraser
            self._set_interactive_mode_visual(self.pen_action)
            self.pen_tool_selected.emit(True)

    @Slot()
    def _on_eraser_select(self):
        """
        Handle eraser tool selection with toggle behavior.

        If eraser is already selected, deselects it. Otherwise, selects eraser
        and deselects pen (mutual exclusivity).
        """
        # Toggle: if eraser is already active, deselect it
        if self._current_mode_action is self.eraser_action:
            self._set_interactive_mode_visual(None)
            self.eraser_tool_selected.emit(False)
        else:
            # Select eraser and deselect pen
            self._set_interactive_mode_visual(self.eraser_action)
            self.eraser_tool_selected.emit(True)

    @Slot()
    def _on_color_picker(self):
        """Placeholder slot for color picker action."""
        print("[TabletHelper] DEBUG: Color Picker action triggered")
        self.color_picker_selected.emit()

    @Slot()
    def _on_orientation_change(self):
        """Placeholder slot for orientation change action."""
        # Get the actual current orientation from the toolbar
        current_orientation = self.orientation()
        # Toggle to the opposite orientation
        new_orientation = Qt.Vertical if (current_orientation == Qt.Horizontal) else Qt.Horizontal
        orientation_str = "Horizontal" if (new_orientation == Qt.Horizontal) else "Vertical"
        print(f"[TabletHelper] DEBUG: Orientation Change action triggered (switching to {orientation_str})")
        self.set_orientation(new_orientation)
        self.orientation_changed.emit(self.orientation())

    @Slot(int)
    def _on_pen_width_changed(self, width):
        """
        Handle pen width change and update icon dynamically.

        When pen width changes, the icon updates to reflect the size,
        and the pen tool is automatically selected.

        Args:
            width: New pen width value
        """
        # Update slider value if it exists (avoid recursion)
        if self._pen_width_slider and self._pen_width_slider.value() != width:
            self._pen_width_slider.setValue(width)

        # Calculate icon index and update icon
        icon_index = self._calculate_icon_index(width, DEFAULT_MAX_PEN_WIDTH)
        icon_path = f"brush_{icon_index}.png"
        self.pen_size_action.setIcon(_load_icon(icon_path))

        # Automatically select pen tool when size changes
        self._set_interactive_mode_visual(self.pen_action)

        print(f"[TabletHelper] DEBUG: Pen Width changed to {width}, icon: {icon_path}")
        self.pen_width_changed.emit(width)
        self.pen_tool_selected.emit(True)

    @Slot(int)
    def _on_eraser_width_changed(self, width):
        """
        Handle eraser width change and update icon dynamically.

        When eraser width changes, the icon updates to reflect the size,
        and the eraser tool is automatically selected.

        Args:
            width: New eraser width value
        """
        # Update slider value if it exists (avoid recursion)
        if self._erase_width_slider and self._erase_width_slider.value() != width:
            self._erase_width_slider.setValue(width)

        # Calculate icon index and update icon
        icon_index = self._calculate_icon_index(width, DEFAULT_MAX_ERASER_WIDTH)
        icon_path = f"eraser_{icon_index}.png"
        self.eraser_size_action.setIcon(_load_icon(icon_path))

        # Automatically select eraser tool when size changes
        self._set_interactive_mode_visual(self.eraser_action)

        print(f"[TabletHelper] DEBUG: Eraser Width changed to {width}, icon: {icon_path}")
        self.eraser_width_changed.emit(width)
        self.eraser_tool_selected.emit(True)

    @Slot(int)
    def _on_contrast_changed(self, value):
        """
        Placeholder slot for contrast change.

        Args:
            value: New contrast value
        """
        contrast_value = value / 100.0
        print(f"[TabletHelper] DEBUG: Contrast changed to {contrast_value:.2f} (raw value: {value})")
        self.contrast_changed.emit(contrast_value)
