"""
Anthropic chat client + tool-use loop.

Network calls run on a worker QThread so the UI stays responsive. Every RPA
tool invocation is marshalled back to the main thread because RPA / Qt are
main-thread-only. The cross-thread handoff uses a queued Qt signal that
carries a request dict + a ``threading.Event`` the worker waits on, which
avoids the PySide2/PySide6 incompatibilities of ``QMetaObject.invokeMethod``
with ``Q_RETURN_ARG``.
"""
import threading

from rpa.utils.qt import QtCore

from . import tool_bridge
from ._log import log, log_exc


DEFAULT_MODEL = "claude-haiku-4-5-20251001"
DEFAULT_MAX_TOOL_ITERATIONS = 25
DEFAULT_MAX_TOKENS = 4096

SYSTEM_PROMPT = (
    "You are an assistant embedded in the ORI Shared Platform RPA review "
    "application. You can drive the app by calling the provided RPA tools "
    "(session, timeline, annotation, color, viewport). Prefer tool calls "
    "over guessing. When the user describes intent (e.g. 'go to the next "
    "clip', 'show me red channel only'), pick the right tool and call it. "
    "After acting, confirm what you did in one short sentence. If a tool "
    "returns an error, read it carefully and either retry with corrected "
    "arguments or report the failure plainly."
)


class _ToolRunner(QtCore.QObject):
    """Lives on the main thread. Worker threads request a tool call by
    emitting :pyattr:`SIG_REQUEST` with a request dict containing
    ``name``, ``args``, ``result`` (filled in by us), and ``event``
    (a ``threading.Event`` we set when done)."""

    SIG_REQUEST = QtCore.Signal(object)

    def __init__(self, rpa, parent=None):
        super().__init__(parent)
        self._rpa = rpa
        self.SIG_REQUEST.connect(self._handle, QtCore.Qt.QueuedConnection)

    @QtCore.Slot(object)
    def _handle(self, req):
        try:
            text = tool_bridge.call_tool(
                self._rpa, req["name"], req["args"] or {})
            req["result"] = {"ok": True, "text": text}
        except Exception as exc:  # noqa: BLE001 - surface every error to LLM
            req["result"] = {
                "ok": False,
                "text": f"{type(exc).__name__}: {exc}",
            }
        finally:
            req["event"].set()

    def run_blocking(self, name, args, timeout=120.0):
        req = {
            "name": name,
            "args": args,
            "event": threading.Event(),
            "result": None,
        }
        self.SIG_REQUEST.emit(req)
        if not req["event"].wait(timeout=timeout):
            return {"ok": False,
                    "text": f"Tool '{name}' timed out after {timeout}s."}
        return req["result"]


class _ChatWorker(QtCore.QObject):
    """Runs the tool-use loop against the Anthropic API on a worker thread."""

    SIG_ASSISTANT_TEXT = QtCore.Signal(str)
    SIG_TOOL_CALL = QtCore.Signal(str, object)
    SIG_TOOL_RESULT = QtCore.Signal(str, str, bool)  # name, text, is_error
    SIG_DONE = QtCore.Signal()
    SIG_ERROR = QtCore.Signal(str)

    def __init__(self, tool_runner):
        super().__init__()
        self._tool_runner = tool_runner
        self._api_key = ""
        self._model = DEFAULT_MODEL
        self._tools = []
        self._system = SYSTEM_PROMPT
        self._max_iters = DEFAULT_MAX_TOOL_ITERATIONS
        self._messages: list = []
        self._cancel = False

    @QtCore.Slot(object)
    def configure(self, cfg):
        self._api_key = cfg.get("api_key", self._api_key)
        self._model = cfg.get("model", self._model)
        if "tools" in cfg:
            self._tools = cfg["tools"]
        if "max_iters" in cfg:
            self._max_iters = int(cfg["max_iters"])

    @QtCore.Slot()
    def cancel(self):
        self._cancel = True

    @QtCore.Slot()
    def reset(self):
        self._messages = []

    @QtCore.Slot(str)
    def send(self, user_text):
        self._cancel = False
        try:
            import anthropic  # lazy: missing dep must not break app start
        except ImportError as exc:
            self.SIG_ERROR.emit(
                "anthropic SDK is not installed. Run "
                "`python rpa/dev_setup.py install-deps` to install it. "
                f"({exc})")
            self.SIG_DONE.emit()
            return

        if not self._api_key:
            self.SIG_ERROR.emit(
                "No Anthropic API key set. Use the AI Chat settings (⚙), "
                "the --anthropic-api-key flag, or $ANTHROPIC_API_KEY.")
            self.SIG_DONE.emit()
            return

        try:
            client = anthropic.Anthropic(api_key=self._api_key)
        except Exception as exc:  # noqa: BLE001
            self.SIG_ERROR.emit(f"Anthropic client init failed: {exc}")
            self.SIG_DONE.emit()
            return

        self._messages.append({"role": "user", "content": user_text})

        try:
            iterations_used = 0
            while iterations_used < self._max_iters:
                iterations_used += 1
                if self._cancel:
                    break

                # Prompt caching: mark the system prompt and the tool list
                # as a cache breakpoint. Anthropic caches everything up to
                # and including the marked block for ~5 min, billing cache
                # hits at ~10% of normal input price and counting them only
                # lightly against the ITPM bucket. The static system + tools
                # blob is by far the largest part of every request, so this
                # cuts both latency and rate-limit pressure dramatically.
                cached_system = [{
                    "type": "text",
                    "text": self._system,
                    "cache_control": {"type": "ephemeral"},
                }]
                cached_tools = list(self._tools)
                if cached_tools:
                    # Copy the last tool dict before mutating to avoid
                    # accidentally caching cache_control into our registry.
                    cached_tools[-1] = {
                        **cached_tools[-1],
                        "cache_control": {"type": "ephemeral"},
                    }
                response = client.messages.create(
                    model=self._model,
                    max_tokens=DEFAULT_MAX_TOKENS,
                    system=cached_system,
                    tools=cached_tools,
                    messages=self._messages,
                )

                try:
                    u = response.usage
                    log(
                        f"usage: in={getattr(u, 'input_tokens', '?')} "
                        f"out={getattr(u, 'output_tokens', '?')} "
                        f"cache_create={getattr(u, 'cache_creation_input_tokens', '?')} "
                        f"cache_read={getattr(u, 'cache_read_input_tokens', '?')} "
                        f"stop={response.stop_reason}"
                    )
                except Exception:
                    pass

                assistant_blocks = []
                for block in response.content:
                    btype = getattr(block, "type", None)
                    if btype == "text":
                        text = getattr(block, "text", "") or ""
                        if text:
                            self.SIG_ASSISTANT_TEXT.emit(text)
                        assistant_blocks.append(
                            {"type": "text", "text": text})
                    elif btype == "tool_use":
                        assistant_blocks.append({
                            "type": "tool_use",
                            "id": block.id,
                            "name": block.name,
                            "input": block.input or {},
                        })
                self._messages.append(
                    {"role": "assistant", "content": assistant_blocks})

                if response.stop_reason != "tool_use":
                    break

                tool_results = []
                for block in assistant_blocks:
                    if block.get("type") != "tool_use":
                        continue
                    if self._cancel:
                        break
                    name = block["name"]
                    args = block["input"] or {}
                    self.SIG_TOOL_CALL.emit(name, dict(args))
                    outcome = self._tool_runner.run_blocking(name, args)
                    if not isinstance(outcome, dict):
                        outcome = {"ok": False, "text": "<no result>"}
                    self.SIG_TOOL_RESULT.emit(
                        name, outcome["text"], not outcome["ok"])
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block["id"],
                        "content": outcome["text"],
                        "is_error": not outcome["ok"],
                    })

                if not tool_results:
                    break
                self._messages.append(
                    {"role": "user", "content": tool_results})
            else:
                # Loop exited normally because the cap was hit (Python's
                # while-else fires when the condition becomes false without
                # a break).
                pass

            if iterations_used >= self._max_iters:
                self.SIG_ERROR.emit(
                    f"Tool-use loop hit cap of {self._max_iters} iterations.")
        except Exception as exc:  # noqa: BLE001
            self.SIG_ERROR.emit(f"{type(exc).__name__}: {exc}")
        finally:
            self.SIG_DONE.emit()


class ChatClient(QtCore.QObject):
    """Public-facing chat client. Owns the worker thread and tool runner.

    The worker thread is started lazily on the first ``send()`` so a misbehaving
    plugin init can't strand a thread."""

    SIG_ASSISTANT_TEXT = QtCore.Signal(str)
    SIG_TOOL_CALL = QtCore.Signal(str, object)
    SIG_TOOL_RESULT = QtCore.Signal(str, str, bool)
    SIG_DONE = QtCore.Signal()
    SIG_ERROR = QtCore.Signal(str)

    _SIG_SEND = QtCore.Signal(str)
    _SIG_CONFIGURE = QtCore.Signal(object)
    _SIG_RESET = QtCore.Signal()

    def __init__(self, rpa, api_key=None, model=DEFAULT_MODEL,
                 max_iters=DEFAULT_MAX_TOOL_ITERATIONS, parent=None):
        log("ChatClient.__init__ start")
        super().__init__(parent)
        self._rpa = rpa
        self._api_key = api_key or ""
        self._model = model
        self._max_iters = max_iters
        try:
            log("building RPA tool schemas")
            self._tools = tool_bridge.build_tools(rpa)
            log(f"built {len(self._tools)} tool schemas")
        except Exception as exc:  # noqa: BLE001
            log_exc("tool_bridge.build_tools failed")
            self._tools = []
            self._tool_build_error = str(exc)
        else:
            self._tool_build_error = ""

        try:
            log("constructing _ToolRunner")
            self._tool_runner = _ToolRunner(rpa, parent=self)
            log("constructing QThread + _ChatWorker")
            self._thread = QtCore.QThread(self)
            self._worker = _ChatWorker(self._tool_runner)
            self._worker.moveToThread(self._thread)
            log("worker moved to thread")
        except Exception:
            log_exc("FATAL: thread/worker setup failed")
            raise

        try:
            self._SIG_SEND.connect(self._worker.send)
            self._SIG_CONFIGURE.connect(self._worker.configure)
            self._SIG_RESET.connect(self._worker.reset)
            self._cancel_proxy = self._worker.cancel
            self._worker.SIG_ASSISTANT_TEXT.connect(self.SIG_ASSISTANT_TEXT)
            self._worker.SIG_TOOL_CALL.connect(self.SIG_TOOL_CALL)
            self._worker.SIG_TOOL_RESULT.connect(self.SIG_TOOL_RESULT)
            self._worker.SIG_DONE.connect(self.SIG_DONE)
            self._worker.SIG_ERROR.connect(self.SIG_ERROR)
            log("ChatClient signals wired")
        except Exception:
            log_exc("FATAL: ChatClient signal wiring failed")
            raise
        log("ChatClient.__init__ DONE")

    def tool_count(self) -> int:
        return len(self._tools)

    def tool_build_error(self) -> str:
        return self._tool_build_error

    def _ensure_thread(self):
        if not self._thread.isRunning():
            self._thread.start()

    def _push_config(self):
        self._SIG_CONFIGURE.emit({
            "api_key": self._api_key,
            "model": self._model,
            "tools": self._tools,
            "max_iters": self._max_iters,
        })

    def set_api_key(self, api_key):
        self._api_key = api_key or ""
        if self._thread.isRunning():
            self._push_config()

    def set_model(self, model):
        self._model = model or DEFAULT_MODEL
        if self._thread.isRunning():
            self._push_config()

    def send(self, user_text):
        self._ensure_thread()
        self._push_config()
        self._SIG_SEND.emit(user_text)

    def cancel(self):
        # DirectConnection-equivalent: just flip the flag on the worker. The
        # worker reads it between iterations.
        self._cancel_proxy()

    def reset(self):
        self._SIG_RESET.emit()

    def shutdown(self):
        if self._thread.isRunning():
            self._thread.quit()
            self._thread.wait(2000)
