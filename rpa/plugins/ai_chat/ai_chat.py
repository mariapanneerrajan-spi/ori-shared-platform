"""
AI Chat plugin entry point.

Heavily instrumented with file logging (see ``widget/_log.py``) so a failure
inside this plugin's init can be diagnosed from
``~/.rpa_app/ai_chat.log`` instead of disappearing into a Windows window-less
crash.

All non-trivial imports are deferred into :py:meth:`AiChat.app_init` so a bad
import doesn't prevent the module from loading and reporting the failure.
"""
# Logger first; absolutely nothing else above this can fail without us
# noticing, because the logger is the only window we have into a hung launch.
from ai_chat.widget._log import log, log_exc, log_banner, log_path

try:
    log_banner("ai_chat module import")
except Exception:
    pass

try:
    from rpa.utils.qt import QtCore, QtGui  # noqa: E402
    log("imported rpa.utils.qt OK")
except Exception:
    log_exc("FATAL: failed to import rpa.utils.qt")
    raise


class AiChat(QtCore.QObject):

    def __init__(self):
        super().__init__()
        self.__panel = None
        self.__dock_widget = None
        self.__toggle_action = None
        log("AiChat.__init__ done")

    def app_init(self, rpa_app):
        log(f"AiChat.app_init start; log file = {log_path()}")
        try:
            self.__rpa = rpa_app.rpa
            self.__main_window = rpa_app.main_window
            self.__cmd_line_args = rpa_app.cmd_line_args
            log(f"got rpa_app fields: rpa={type(self.__rpa).__name__} "
                f"main_window={type(self.__main_window).__name__}")
        except Exception:
            log_exc("FATAL: rpa_app field access failed")
            return

        try:
            log("importing ItvDockWidget")
            from rpa.app.widgets.itv_dock_widget import ItvDockWidget
            log("ItvDockWidget imported OK")
        except Exception:
            log_exc("FATAL: ItvDockWidget import failed; plugin disabled")
            return

        try:
            log("importing AiChatPanel")
            from ai_chat.widget.ai_chat_panel import AiChatPanel
            log("AiChatPanel imported OK")
        except Exception:
            log_exc("FATAL: AiChatPanel import failed; plugin disabled")
            return

        try:
            log("constructing AiChatPanel")
            self.__panel = AiChatPanel(self.__rpa, self.__main_window)
            log("AiChatPanel constructed OK")
        except Exception:
            log_exc("FATAL: AiChatPanel construction failed; plugin disabled")
            self.__panel = None
            return

        try:
            log("constructing ItvDockWidget")
            self.__dock_widget = ItvDockWidget("AI Chat", self.__main_window)
            self.__dock_widget.setWidget(self.__panel)
            log("adding dock widget to main window")
            self.__main_window.addDockWidget(
                QtCore.Qt.RightDockWidgetArea, self.__dock_widget)
            self.__dock_widget.hide()
            log("dock widget attached + hidden")
        except Exception:
            log_exc("FATAL: dock widget setup failed; plugin disabled")
            return

        try:
            log("wiring toggle action + Help menu entry")
            self.__toggle_action = self.__dock_widget.toggleViewAction()
            self.__toggle_action.setShortcut(QtGui.QKeySequence("Shift+A"))
            self.__toggle_action.setProperty("hotkey_editor", True)
            help_menu = self.__main_window.get_menu("Help")
            help_menu.addSeparator()
            help_menu.addAction(self.__toggle_action)
            log("Help menu entry added")
        except Exception:
            log_exc("non-fatal: menu wiring failed; panel still usable")

        log("AiChat.app_init DONE")

    def post_app_init(self):
        log("AiChat.post_app_init start")
        if self.__panel is None:
            log("post_app_init: panel is None, skipping CLI overrides")
            return
        try:
            api_key = getattr(self.__cmd_line_args, "anthropic_api_key", None)
            if api_key:
                self.__panel.set_api_key(api_key)
                log("post_app_init: applied --anthropic-api-key")
            model = getattr(self.__cmd_line_args, "ai_model", None)
            if model:
                self.__panel.set_model(model)
                log(f"post_app_init: applied --ai-model={model}")
        except Exception:
            log_exc("non-fatal: post_app_init CLI override failed")
        log("AiChat.post_app_init DONE")
