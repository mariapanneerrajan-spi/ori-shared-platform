
import os
from Itview.Manifest import QtCore, QtGui
from Itview import QT4Color
from Itview import constants as C

DISP_OVERLAY_ENV_NAME = 'TABLETHELPER_NOHIDE_OVERLAYS'
KEY_OVERRIDE_NAME     = 'TABLETHELPER_KEY_OVERRIDE'

ICON_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), 'icons')

class TabletHelper(QtCore.QObject):
    TOGGLE_ON_COLOR = (0.63, 0.63, 0.63)
    def itvPluginInitialize(self, info):
        if not hasattr(info, 'itview_app'): return
        self.__itview_api = info.itview_app.getAPI("v1")
        self.__toolbar = None
        self.__dimLights = False
        self.__audioWaveformPlugin = False
        self.__menu = None
        self.__plugins = None
        self.__photoPlugin = False
        self.__frameOverlay = False
        self.__textOverlay = False
        self.annotationColor = []
        self.__menu = None
        self.__plugins = None
        self.__audioScrubbing = False
        self.__toggleMask = False
        self.__orientHorizontal = False
        self.annotationColor = []
        self.annotationColor.append((1.0, 1.0, 1.0))
        self.annotationColor.append((1.0, 0.0, 0.0))
        self.annotationColor.append((0.9, 0.5, 0.0))
        self.annotationColor.append((0.3, 1.0, 0.9))
        self.defaultAnnoColor = self.annotationColor[0]
        self.colorIter = 0
        self.modeActions = []

        TabletHelper.PREF_PLUGIN = 'TabletHelper'
        TabletHelper.PREF_TOOLBAR_POSITION_X = '{}/geometry/x'.format(TabletHelper.PREF_PLUGIN)
        TabletHelper.PREF_TOOLBAR_POSITION_Y = '{}/geometry/y'.format(TabletHelper.PREF_PLUGIN)
        TabletHelper.PREF_TOOLBAR_ORIENTATION = '{}/orientation'.format(TabletHelper.PREF_PLUGIN)

        group = self.__itview_api.createCommandLineOptionGroup('TabletHelper')
        group.add_option(
            "--tablet",
            action="store_true",
            dest="TabletHelper_activate",
            help="Enable the Tablet Helper Buttons",
        )
        self.__itview_api.addCommandLineOptionGroup(group)
        self.__initToolbar()

    def itvAttachMenu_v3(self, menus):
        self.__menu = menus
        keySeq = os.environ.get(KEY_OVERRIDE_NAME, 'Ctrl+Alt+T')
        menu = menus['Plugins']
        menu.addAction("Tablet Helper", self.toolbarCallback,
                        QtGui.QKeySequence(keySeq))

    def itvProcessCommandLine(self, options):
        if options.TabletHelper_activate is not None:
            self.toolbarCallback()

    def __initActions(self):
        self.colorAction = QtGui.QAction(QtGui.QIcon("{icons}/applications-graphics".format(icons=ICON_PATH)), "Cycle Annotation Color", self)
        self.clearAnnoAction = QtGui.QAction(QtGui.QIcon("{icons}/edit-clear".format(icons=ICON_PATH)), "Clear Annotations", self)
        self.undoAnnoAction = QtGui.QAction(QtGui.QIcon("{icons}/edit-undo".format(icons=ICON_PATH)), "Undo Annotation", self)
        self.redoAnnoAction = QtGui.QAction(QtGui.QIcon("{icons}/edit-redo".format(icons=ICON_PATH)), "Redo Annotation", self)
        self.muteAction = QtGui.QAction(QtGui.QIcon("{icons}/audio-volume-muted".format(icons=ICON_PATH)), "Mute Audio", self)
        self.nextClipAction = QtGui.QAction(QtGui.QIcon("{icons}/go-next".format(icons=ICON_PATH)), "Next Clip", self)#go-last-view
        self.prevClipAction = QtGui.QAction(QtGui.QIcon("{icons}/go-previous".format(icons=ICON_PATH)), "Previous Clip", self)#go-first-view
        self.nextAnnoAction = QtGui.QAction(QtGui.QIcon("{icons}/arrow-right-double".format(icons=ICON_PATH)), "Next Annotation", self)
        self.prevAnnoAction = QtGui.QAction(QtGui.QIcon("{icons}/arrow-left-double".format(icons=ICON_PATH)), "Previous Annotation", self)
        self.dimAction = QtGui.QAction(QtGui.QIcon("{icons}/help-hint".format(icons=ICON_PATH)), "Dim Lights", self)
        self.audioWFAction = QtGui.QAction(QtGui.QIcon("{icons}/applications-multimedia".format(icons=ICON_PATH)), "Audio Waveforms", self)
        self.colorSwatchAction = QtGui.QAction(QtGui.QIcon("{icons}/fill-color".format(icons=ICON_PATH)), "Color Swatch", self)
        self.photoAction = QtGui.QAction(QtGui.QIcon("{icons}/preferences-desktop-user".format(icons=ICON_PATH)), "Photo Plugin", self)
        self.frameAction = QtGui.QAction(QtGui.QIcon("{icons}/frame-overlay".format(icons=ICON_PATH)), "Display frame overlay", self)
        self.textAction = QtGui.QAction(QtGui.QIcon("{icons}/text-overlay".format(icons=ICON_PATH)), "Display text overlay", self)
        self.overlayAction = QtGui.QAction(QtGui.QIcon("{icons}/all-overlay".format(icons=ICON_PATH)), "Display all overlays", self)
        self.scrubAction = QtGui.QAction(QtGui.QIcon("{icons}/applications-media-scrub".format(icons=ICON_PATH)), "Play audio while scrubbing", self)
        self.maskAction = QtGui.QAction(QtGui.QIcon("{icons}/insert-image".format(icons=ICON_PATH)), "Toggle Mask", self)
        self.penAction = QtGui.QAction(QtGui.QIcon("{icons}/draw-freehand".format(icons=ICON_PATH)), "Pen Tool", self)
        self.eraserAction = QtGui.QAction(QtGui.QIcon("{icons}/draw-eraser".format(icons=ICON_PATH)), "Eraser Tool", self)
        self.colorPickAction = QtGui.QAction(QtGui.QIcon("{icons}/color-picker".format(icons=ICON_PATH)), "Color Picker", self)
        self.orientAction = QtGui.QAction(QtGui.QIcon("{icons}/orient-horizontal".format(icons=ICON_PATH)), "Change Toolbar Orientation", self)

        self.createPenSizeSlider()
        self.createEraserSlider()
        self.createContrastSlider()
        self.__itview_api.SIG_INTERACTIVE_MODE_CHANGED.connect(self.syncSelect)

        self.connect(self.colorAction, QtCore.SIGNAL("triggered()"), self.cycleColor)
        self.connect(self.clearAnnoAction, QtCore.SIGNAL("triggered()"), self.__itview_api.clearAllAnnotations)
        self.connect(self.undoAnnoAction, QtCore.SIGNAL("triggered()"), self.__itview_api.undoAnnotationStroke)
        self.connect(self.redoAnnoAction, QtCore.SIGNAL("triggered()"), self.__itview_api.redoAnnotationStroke)
        self.connect(self.muteAction, QtCore.SIGNAL("triggered()"), lambda: self.__itview_api.setAudioMute(not self.__itview_api.getAudioMute()))
        self.connect(self.nextClipAction, QtCore.SIGNAL("triggered()"), self.__itview_api.gotoNextClip)
        self.connect(self.prevClipAction, QtCore.SIGNAL("triggered()"), self.__itview_api.gotoPrevClip)
        self.connect(self.nextAnnoAction, QtCore.SIGNAL("triggered()"), self.__itview_api.nextAnnotation)
        self.connect(self.prevAnnoAction, QtCore.SIGNAL("triggered()"), self.__itview_api.prevAnnotation)
        self.connect(self.dimAction, QtCore.SIGNAL("triggered()"), self.dimLights)
        self.connect(self.audioWFAction, QtCore.SIGNAL("triggered()"), self.audioWaveformPlugin)
        self.connect(self.colorSwatchAction, QtCore.SIGNAL("triggered()"), self.colorSwatch)
        self.connect(self.photoAction, QtCore.SIGNAL("triggered()"), self.photoPlugin)
        self.connect(self.frameAction, QtCore.SIGNAL("triggered()"), self.frameOverlay)
        self.connect(self.textAction, QtCore.SIGNAL("triggered()"), self.textOverlay)
        self.connect(self.overlayAction, QtCore.SIGNAL("triggered()"), self.allOverlay)
        self.connect(self.scrubAction, QtCore.SIGNAL("triggered()"), self.audioScrub)
        self.connect(self.maskAction, QtCore.SIGNAL("triggered()"), self.toggleMask)
        self.connect(self.penAction, QtCore.SIGNAL("triggered()"), self.penSelect)
        self.connect(self.eraserAction, QtCore.SIGNAL("triggered()"), self.eraserSelect)
        self.connect(self.colorPickAction, QtCore.SIGNAL("triggered()"), self.__itview_api.SIG_ANNOTATION_PEN_COLOR_TOOL_SELECTED.emit)
        self.connect(self.orientAction, QtCore.SIGNAL("triggered()"), self.orientChange)
        self.connect(self.contrastAction, QtCore.SIGNAL("triggered()"), self.contrastSet)

        self.__itview_api.SIG_VOLUME_MUTE_CHANGED.connect(self.muteHandler)

        self.modeActions.extend([self.penAction, self.eraserAction])

    def __initToolbar(self):
        self.__initActions()
        self.__toolbar = QtGui.QToolBar("Tablet Helper", self.__itview_api.getViewerWidget())
        self.__toolbar.setObjectName("TabletHelper")
        self.__toolbar.addAction(self.orientAction)
        self.__toolbar.addAction(self.dimAction)
        self.__toolbar.addWidget(self.contrastAction)
        self.__toolbar.addAction(self.colorAction)
        self.__toolbar.addAction(self.colorPickAction)
        self.__toolbar.addAction(self.penAction)
        self.__toolbar.addWidget(self.penSizeAction)
        self.__toolbar.addAction(self.eraserAction)
        self.__toolbar.addWidget(self.eraserSizeAction)
        self.__toolbar.addAction(self.clearAnnoAction)
        self.__toolbar.addAction(self.undoAnnoAction)
        self.__toolbar.addAction(self.redoAnnoAction)
        self.__toolbar.addAction(self.prevAnnoAction)
        self.__toolbar.addAction(self.nextAnnoAction)
        self.__toolbar.addAction(self.prevClipAction)
        self.__toolbar.addAction(self.nextClipAction)
        self.__toolbar.addAction(self.muteAction)
        self.__toolbar.addAction(self.scrubAction)
        self.__toolbar.addAction(self.maskAction)
        self.__toolbar.addAction(self.audioWFAction)
        self.__toolbar.addAction(self.colorSwatchAction)
        self.__toolbar.addAction(self.photoAction)
        self.__toolbar.addAction(self.frameAction)
        self.__toolbar.addAction(self.textAction)
        self.__toolbar.addAction(self.overlayAction)
        self.__toolbar.setWindowFlags(QtCore.Qt.Tool|QtCore.Qt.WindowStaysOnTopHint|\
               QtCore.Qt.FramelessWindowHint|QtCore.Qt.X11BypassWindowManagerHint)

        self.__toolbar.widgetForAction(self.photoAction).setAutoFillBackground(True)
        self.__toolbar.widgetForAction(self.scrubAction).setAutoFillBackground(True)
        self.__toolbar.widgetForAction(self.maskAction).setAutoFillBackground(True)
        self.__toolbar.widgetForAction(self.audioWFAction).setAutoFillBackground(True)
        self.__toolbar.widgetForAction(self.photoAction).setAutoFillBackground(True)
        self.__toolbar.widgetForAction(self.textAction).setAutoFillBackground(True)
        self.__toolbar.widgetForAction(self.colorAction).setAutoFillBackground(True)
        self.__toolbar.widgetForAction(self.penAction).setAutoFillBackground(True)
        self.__toolbar.widgetForAction(self.eraserAction).setAutoFillBackground(True)
        frameWidget = self.__toolbar.widgetForAction(self.frameAction)
        frameWidget.setAutoFillBackground(True)

        self.__toolbar.setIconSize(QtCore.QSize(16, 16))

        palette = frameWidget.palette().color(frameWidget.backgroundRole())
        self.defaultColor = (palette.red() / float(255),
                             palette.blue() / float(255),
                             palette.green() / float(255))
        self.muteHandler(self.__itview_api.getAudioMute())

        for action in self.__toolbar.actions():
            widget = self.__toolbar.widgetForAction(action)
            widget.setFocusPolicy(QtCore.Qt.NoFocus)

    def drawToolbar(self, orientation=QtCore.Qt.Vertical):
        self.__toolbar.hide()
        self.__toolbar.setOrientation(orientation)
        self.__toolbar.show()

    def toolbarCallback(self):
        self.setColorDefault()
        userActions = self.__itview_api.getUserActions()
        self.__plugins = self.__menu['Plugins']

        if self.__toolbar is None:
            self.__initToolbar()

        if self.__toolbar.isHidden() or not self.__itview_api.getFullScreen():
            self.__toolbar.setMovable(True)
            self.__toolbar.setFocusPolicy(QtCore.Qt.NoFocus)

            orient, _ = self.__itview_api.readPreferencesEntry(
                TabletHelper.PREF_TOOLBAR_ORIENTATION, default_value=QtCore.Qt.Vertical)
            orient = int(orient)
            self.__orientHorizontal = orient == QtCore.Qt.Horizontal
            self.drawToolbar(orient)

            x_coor, _ = self.__itview_api.readPreferencesEntry(
                TabletHelper.PREF_TOOLBAR_POSITION_X, default_value=None)
            y_coor, _ = self.__itview_api.readPreferencesEntry(
                TabletHelper.PREF_TOOLBAR_POSITION_Y, default_value=None)

            if x_coor is None and y_coor is None:
                # Initial placement of toolbar
                desktop = QtGui.QDesktopWidget().screenGeometry(
                    self.__itview_api.getViewerWidget())
                x_coor = desktop.topRight().x() - (self.__toolbar.width() - 1)
                y_coor = (desktop.bottomRight().y() - self.__toolbar.height()) / 2
            else:
                x_coor = int(x_coor)
                y_coor = int(y_coor)
            self.__toolbar.move(QtCore.QPoint(x_coor, y_coor))

            userActions.toggle_full_screen.setOn(True)
            userActions.toggle_info_bar.setOn(False)
            userActions.show_toolbar.setOn(True)
            userActions.show_timeline.setOn(True)
            userActions.show_annotations.setOn(True)

            self.eraserWidth(self.__itview_api.getAnnotationEraserWidth())
            self.penWidth(self.__itview_api.getAnnotationPenWidth())

            self.orientIconSet()
            if not os.environ.get(DISP_OVERLAY_ENV_NAME, False):
                userActions.overlay_frame.setOn(False)
                userActions.overlay_frame.setOn(False)
                userActions.overlay_text.setOn(False)
        else:
            self.__toolbar.hide()
            userActions.show_toolbar.setOn(False)
            userActions.show_timeline.setOn(False)
            userActions.show_annotations.setOn(False)
            userActions.toggle_pen.setOn(False)

            self.savePreferences()

    def setColorDefault(self):
        color = self.__itview_api.getAnnotationPenColor()
        qcolor = QtGui.QColor(*map(lambda x: int(x*255), color))
        colorWidget = self.__toolbar.widgetForAction(self.colorAction)
        palette = colorWidget.palette()
        palette.setColor(colorWidget.backgroundRole(), qcolor)
        colorWidget.setPalette(palette)

    def cycleColor(self):
        self.colorIter += 1
        if self.colorIter == len(self.annotationColor):
            self.colorIter = 0
        color = self.annotationColor[self.colorIter]
        qcolor = QtGui.QColor(*map(lambda x: int(x*255), color))
        self.__itview_api.setAnnotationPenColor(color)

        colorWidget = self.__toolbar.widgetForAction(self.colorAction)
        palette = colorWidget.palette()
        palette.setColor(colorWidget.backgroundRole(), qcolor)
        colorWidget.setPalette(palette)

    def dimLights(self):
        self.__dimLights = not self.__dimLights
        cc = QT4Color.ASCColorCorrector.MutableCDLTransform()
        if self.__dimLights:
            # print "Dimming the lights..."
            cc.setSlope([0.65,0.65,0.65])
            cc.setSat(0.5)
            qicon = QtGui.QIcon("{icons}/help-hint-dull".format(icons=ICON_PATH))
        else:
            cc.setSlope([1,1,1])
            cc.setSat(1)
            qicon = QtGui.QIcon("{icons}/help-hint".format(icons=ICON_PATH))
            # print "Raising the lights..."
        self.__itview_api.setCurrentColorCorrection(cc)
        self.dimAction.setIcon(qicon)

    def audioScrub(self):
        self.__audioScrubbing = not self.__audioScrubbing
        if self.__audioScrubbing:
            qcolor = QtGui.QColor(*map(lambda x: int(x * 255), self.TOGGLE_ON_COLOR))
        else:
            qcolor = QtGui.QColor(*map(lambda x: int(x * 255), self.defaultColor))
        widget = self.__toolbar.widgetForAction(self.scrubAction)
        palette = widget.palette()
        palette.setColor(widget.backgroundRole(), qcolor)
        widget.setPalette(palette)
        self.__itview_api.enableAudioWhileScrubbing(self.__audioScrubbing)

    def toggleMask(self):
        self.__toggleMask = not self.__toggleMask
        if self.__toggleMask:
            qcolor = QtGui.QColor(*map(lambda x: int(x * 255), self.TOGGLE_ON_COLOR))
        else:
            qcolor = QtGui.QColor(*map(lambda x: int(x * 255), self.defaultColor))
        widget = self.__toolbar.widgetForAction(self.maskAction)
        palette = widget.palette()
        palette.setColor(widget.backgroundRole(), qcolor)
        widget.setPalette(palette)
        self.__itview_api.getUserActions().toggle_mask.setOn(self.__toggleMask)

    def audioWaveformPlugin(self):
        self.__audioWaveformPlugin = not self.__audioWaveformPlugin
        if self.__audioWaveformPlugin:
            qcolor = QtGui.QColor(*map(lambda x: int(x * 255), self.TOGGLE_ON_COLOR))
        else:
            qcolor = QtGui.QColor(*map(lambda x: int(x * 255), self.defaultColor))
        widget = self.__toolbar.widgetForAction(self.audioWFAction)
        palette = widget.palette()
        palette.setColor(widget.backgroundRole(), qcolor)
        widget.setPalette(palette)

        actions = self.__plugins.actions()
        for action in actions:
            if str(action.text()) == "Audio Waveform Timeline":
                action.activate(QtGui.QAction.Trigger)
                return
        audioWidget = self.__toolbar.widgetForAction(self.audioWFAction)
        QtGui.QMessageBox.warning(
            audioWidget,
            "ERROR",
            "Audio Waveform (gltimeline) plugin not loaded correctly")

    def colorSwatch(self):
        cur = map(lambda x: int(x * 255), self.__itview_api.getAnnotationPenColor())
        color = QtGui.QColorDialog.getColor(
            QtGui.QColor(*cur),
            self.__itview_api.getDialogParent(),
            "color picker")
        if not color.isValid(): return
        qcolor = (color.red() / 255.0, color.green() / 255.0, color.blue() / 255.0)
        self.__itview_api.setAnnotationPenColor(qcolor)
        widget = self.__toolbar.widgetForAction(self.colorAction)
        palette = widget.palette()
        palette.setColor(widget.backgroundRole(), color)
        widget.setPalette(palette)

    def photoPlugin(self):
        self.__photoPlugin = not self.__photoPlugin
        if self.__photoPlugin:
            qcolor = QtGui.QColor(*map(lambda x: int(x * 255), self.TOGGLE_ON_COLOR))
        else:
            qcolor = QtGui.QColor(*map(lambda x: int(x * 255), self.defaultColor))
        widget = self.__toolbar.widgetForAction(self.photoAction)
        palette = widget.palette()
        palette.setColor(widget.backgroundRole(), qcolor)
        widget.setPalette(palette)

        actions = self.__plugins.actions()
        for action in actions:
            if str(action.text()) == "Photo":
                action.activate(QtGui.QAction.Trigger)
                return
        photoWidget = self.__toolbar.widgetForAction(self.photoAction)
        QtGui.QMessageBox.warning(
            photoWidget,
            "ERROR",
            "Photo plugin not loaded correctly")

    def frameOverlay(self):
        self.__frameOverlay = not self.__frameOverlay
        if self.__frameOverlay:
            qcolor = QtGui.QColor(*map(lambda x: int(x * 255), self.TOGGLE_ON_COLOR))
        else:
            qcolor = QtGui.QColor(*map(lambda x: int(x * 255), self.defaultColor))
        widget = self.__toolbar.widgetForAction(self.frameAction)
        palette = widget.palette()
        palette.setColor(widget.backgroundRole(), qcolor)
        widget.setPalette(palette)

        self.__itview_api.getDisplayFrameOverlay()
        self.__itview_api.setDisplayFrameOverlay(self.__frameOverlay)

    def textOverlay(self):
        self.__textOverlay = not self.__textOverlay
        if self.__textOverlay:
            qcolor = QtGui.QColor(*map(lambda x: int(x * 255), self.TOGGLE_ON_COLOR))
        else:
            qcolor = QtGui.QColor(*map(lambda x: int(x * 255), self.defaultColor))
        widget = self.__toolbar.widgetForAction(self.textAction)
        palette = widget.palette()
        palette.setColor(widget.backgroundRole(), qcolor)
        widget.setPalette(palette)

        self.__itview_api.getDisplayTextOverlay()
        self.__itview_api.setDisplayTextOverlay(self.__textOverlay)

    def allOverlay(self):
        if self.__textOverlay and not self.__frameOverlay:
            self.frameOverlay()
        elif self.__frameOverlay and not self.__textOverlay:
            self.textOverlay()
        else:
            self.frameOverlay()
            self.textOverlay()

    @QtCore.Slot(bool)
    def muteHandler(self, muted):
        if muted:
            self.muteAction.setIcon(QtGui.QIcon("{icons}/audio-volume-muted".format(icons=ICON_PATH)))
        else:
            self.muteAction.setIcon(QtGui.QIcon("{icons}/audio-volume-high".format(icons=ICON_PATH)))

    def createPenSizeSlider(self):
        penSizeMenu = QtGui.QMenu('')
        penSWA = SliderWidgetAction(penSizeMenu,
                                    orientation=QtCore.Qt.Vertical,
                                    minimum=1, maximum=C.MAX_ANNOTATION_PEN_WIDTH,
                                    maximumWidth=20)
        penSizeMenu.addAction(penSWA)
        self.__penWidth_slider = penSWA.getCreatedWidget()
        self.__penWidth_slider.valueChanged.connect(self.penWidth)
        penSizeMenu.setMinimumWidth(self.__penWidth_slider.width() + 6)
        self.penSizeAction = QtGui.QPushButton('', None)
        self.penSizeAction.setToolTip("Pen Size")
        self.penSizeAction.setMenu(penSizeMenu)
        self.__itview_api.SIG_ANNOTATION_PEN_WIDTH_CHANGED.connect(self.penWidth)

    def createEraserSlider(self):
        eraserSizeMenu = QtGui.QMenu('')
        eraserSWA = SliderWidgetAction(eraserSizeMenu,
                            orientation=QtCore.Qt.Vertical,
                            minimum=1, maximum=C.MAX_ANNOTATION_ERASER_WIDTH,
                            maximumWidth=20)
        eraserSizeMenu.addAction(eraserSWA)
        self.__eraseWidth_slider = eraserSWA.getCreatedWidget()
        self.__eraseWidth_slider.valueChanged.connect(self.eraserWidth)
        eraserSizeMenu.setMinimumWidth(self.__eraseWidth_slider.width() + 6)
        self.eraserSizeAction = QtGui.QPushButton('', None)
        self.eraserSizeAction.setToolTip("Eraser Size")
        self.eraserSizeAction.setMenu(eraserSizeMenu)
        self.__itview_api.SIG_ANNOTATION_ERASER_WIDTH_CHANGED.connect(self.eraserWidth)

    def syncSelect(self, mode):
        if mode == C.ITR_MODE_PEN:
            self.setInteractiveMode(self.penAction)
        if mode == C.ITR_MODE_ERASE:
            self.setInteractiveMode(self.eraserAction)

    def penSelect(self):
        if self.__itview_api.getInteractiveMode() == C.ITR_MODE_PEN:
            self.__itview_api.setInteractiveMode(C.ITR_MODE_DEFAULT)
            self.setInteractiveMode(None)
        else:
            self.__itview_api.setInteractiveMode(C.ITR_MODE_PEN)
            self.setInteractiveMode(self.penAction)

    def eraserSelect(self):
        if self.__itview_api.getInteractiveMode() == C.ITR_MODE_ERASE:
            self.__itview_api.setInteractiveMode(C.ITR_MODE_DEFAULT)
            self.setInteractiveMode(None)
        else:
            self.__itview_api.setInteractiveMode(C.ITR_MODE_ERASE)
            self.setInteractiveMode(self.eraserAction)

    def penWidth(self, width):
        self.__itview_api.setAnnotationPenWidth(int(width))
        self.penSizeAction.setIcon(
            QtGui.QIcon("{icons}/brushes/brush_{w}".format(icons=ICON_PATH,
                         w=(width-1)/(C.MAX_ANNOTATION_PEN_WIDTH/10))))
        self.__penWidth_slider.setValue(width)
        self.setInteractiveMode(self.penAction)

    def eraserWidth(self, width):
        self.__itview_api.setAnnotationEraserWidth(int(width))
        self.eraserSizeAction.setIcon(
            QtGui.QIcon("{icons}/erasers/eraser_{w}".format(icons=ICON_PATH,
                         w=(width-1)/(C.MAX_ANNOTATION_ERASER_WIDTH/10))))
        self.__eraseWidth_slider.setValue(width)
        self.setInteractiveMode(self.eraserAction)

    def createContrastSlider(self):
        contrastMenu = QtGui.QMenu('')
        swa = SliderWidgetAction(contrastMenu,
                                 orientation=QtCore.Qt.Vertical,
                                 minimum=0, maximum=80, maximumWidth=20)
        contrastMenu.addAction(swa)
        self.__contrast_slider = swa.getCreatedWidget()
        self.__contrast_slider.valueChanged.connect(self.contrastSet)
        contrastMenu.setMinimumWidth(self.__contrast_slider.width() + 6)
        self.contrastAction = QtGui.QPushButton('', None)
        self.contrastAction.setToolTip("Contrast")
        self.contrastAction.setMenu(contrastMenu)
        self.contrastAction.setIcon(QtGui.QIcon("{icons}/contrast".format(icons=ICON_PATH)))

    def setInteractiveMode(self, curr_action):
        for action in self.modeActions:
            if action is curr_action:
                qcolor = QtGui.QColor(*map(lambda x: int(x * 255), self.TOGGLE_ON_COLOR))
            else:
                qcolor = QtGui.QColor(*map(lambda x: int(x * 255), self.defaultColor))
            widget = self.__toolbar.widgetForAction(action)
            palette = widget.palette()
            palette.setColor(widget.backgroundRole(), qcolor)
            widget.setPalette(palette)

    def orientChange(self):
        self.__orientHorizontal = not self.__orientHorizontal
        if self.__orientHorizontal:
            self.drawToolbar(QtCore.Qt.Horizontal)
        else:
            self.drawToolbar(QtCore.Qt.Vertical)
        self.orientIconSet()

    def orientIconSet(self):
        if self.__toolbar.orientation() == QtCore.Qt.Horizontal:
            self.orientAction.setIcon(
                QtGui.QIcon("{icons}/orient-vertical".format(icons=ICON_PATH)))
        else:
            self.orientAction.setIcon(
                QtGui.QIcon("{icons}/orient-horizontal".format(icons=ICON_PATH)))

    def contrastSet(self, value):
        contrastValue = value / 100.0
        if contrastValue == 0.0:
            lastMixMode = self.__itview_api.getBackgroundMixMode()
            self.__itview_api.setBackgroundMixMode(lastMixMode)

        self.__itview_api.setMixColorValue(
            C.CONTRAST_MIX_COLOR, contrastValue)

    def savePreferences(self):
        self.__itview_api.writePreferencesEntry(
            TabletHelper.PREF_TOOLBAR_POSITION_X,
            self.__toolbar.x())
        self.__itview_api.writePreferencesEntry(
            TabletHelper.PREF_TOOLBAR_POSITION_Y,
            self.__toolbar.y())
        self.__itview_api.writePreferencesEntry(
            TabletHelper.PREF_TOOLBAR_ORIENTATION,
            self.__toolbar.orientation())

class SliderWidgetAction(QtGui.QWidgetAction):
    def __init__(self, parent, orientation=QtCore.Qt.Vertical,
                 minimum=None, maximum=None, tickInterval=None,
                 singleStep=None, maximumWidth=None):
        QtGui.QWidgetAction.__init__(self, parent)

        self.__orientation = orientation
        self.__minimum = minimum
        self.__maximum = maximum
        self.__tickInterval = tickInterval
        self.__singleStep = singleStep
        self.__maximumWidth = maximumWidth

    def createWidget(self, parent):
        slider = QtGui.QSlider(self.__orientation, parent)
        if self.__minimum is not None:
            slider.setMinimum(self.__minimum)
        if self.__maximum is not None:
            slider.setMaximum(self.__maximum)
        if self.__tickInterval is not None:
            slider.setTickInterval(self.__tickInterval)
        if self.__singleStep is not None:
            slider.setSingleStep(self.__singleStep)
        if self.__maximumWidth is not None:
            slider.setMaximumWidth(self.__maximumWidth)
        return slider

    def getCreatedWidget(self):
        widgets = self.createdWidgets()
        assert widgets
        assert len(widgets) == 1
        return widgets[0]