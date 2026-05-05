"""
Reflects RPA's public API modules into Anthropic tool schemas and dispatches
tool calls back into the live RPA instance.

Tool name format: ``<module>__<method>`` (double underscore, because Anthropic
disallows ``.`` in tool names). Example: ``timeline_api__goto_frame``.
"""
import inspect
import typing
from typing import Any


# RPA modules to expose. Mirrors the discovery list in
# rpa_widgets/rpa_interpreter/rpa_interpreter.py.
_RPA_MODULES = (
    "session_api",
    "annotation_api",
    "timeline_api",
    "color_api",
    "viewport_api",
)

# Hard cap on the size of a tool_result payload sent back to the model.
_MAX_RESULT_CHARS = 8000


def _python_type_to_schema(py_type: Any) -> dict:
    """Map a Python annotation to a JSON Schema fragment.

    Falls back to a permissive multi-type schema for anything we cannot resolve,
    so the model can still attempt the call rather than refusing because no
    schema fits.
    """
    permissive = {"type": ["string", "number", "boolean", "object", "array", "null"]}
    if py_type is inspect.Parameter.empty or py_type is Any:
        return permissive

    origin = typing.get_origin(py_type)
    args = typing.get_args(py_type)

    # Optional[X] / Union[X, None] -> use X's schema, mark nullable by adding "null".
    if origin is typing.Union:
        non_none = [a for a in args if a is not type(None)]
        if len(non_none) == 1:
            inner = _python_type_to_schema(non_none[0])
            t = inner.get("type")
            if isinstance(t, str):
                inner["type"] = [t, "null"]
            elif isinstance(t, list) and "null" not in t:
                inner["type"] = t + ["null"]
            return inner
        return permissive

    if origin in (list, tuple, set, frozenset):
        item_schema = _python_type_to_schema(args[0]) if args else {}
        return {"type": "array", "items": item_schema or permissive}

    if origin is dict:
        return {"type": "object"}

    if py_type is bool:
        return {"type": "boolean"}
    if py_type is int:
        return {"type": "integer"}
    if py_type is float:
        return {"type": "number"}
    if py_type is str:
        return {"type": "string"}
    if py_type is list:
        return {"type": "array"}
    if py_type is dict:
        return {"type": "object"}
    if py_type is type(None):
        return {"type": "null"}

    return permissive


def _build_input_schema(method) -> dict:
    """Build a JSON Schema object for ``method``'s parameters."""
    properties: dict = {}
    required: list = []
    try:
        sig = inspect.signature(method)
    except (TypeError, ValueError):
        return {"type": "object", "properties": {}, "additionalProperties": True}

    for name, param in sig.parameters.items():
        if name == "self":
            continue
        if param.kind in (inspect.Parameter.VAR_POSITIONAL,
                          inspect.Parameter.VAR_KEYWORD):
            continue
        properties[name] = _python_type_to_schema(param.annotation)
        if param.default is inspect.Parameter.empty:
            required.append(name)

    schema = {"type": "object", "properties": properties}
    if required:
        schema["required"] = required
    return schema


def _short_description(method, fallback: str) -> str:
    doc = inspect.getdoc(method)
    if not doc:
        return fallback
    # First non-empty line.
    for line in doc.splitlines():
        line = line.strip()
        if line:
            # Anthropic enforces a length cap on descriptions; keep it short.
            return line[:512]
    return fallback


def _is_signal(member) -> bool:
    # Qt Signal instances live on the class as Signal/PyQtSignal descriptors.
    # Be defensive about binding differences.
    cls_name = type(member).__name__
    if cls_name in ("Signal", "SignalInstance", "pyqtSignal", "pyqtBoundSignal"):
        return True
    return False


def build_tools(rpa) -> list:
    """Reflect every public method on each RPA API module as a tool schema.

    Returns a list of dicts in Anthropic's ``tools`` parameter format.
    """
    tools: list = []
    for module_name in _RPA_MODULES:
        module = getattr(rpa, module_name, None)
        if module is None:
            continue
        for attr_name in dir(module):
            if attr_name.startswith("_"):
                continue
            if attr_name.startswith("SIG_"):
                continue
            if attr_name == "delegate_mngr":
                continue
            try:
                member = getattr(module, attr_name)
            except Exception:
                continue
            if _is_signal(member):
                continue
            if not callable(member):
                continue

            tool_name = f"{module_name}__{attr_name}"
            description = _short_description(
                member, fallback=f"{module_name}.{attr_name}")
            tools.append({
                "name": tool_name,
                "description": description,
                "input_schema": _build_input_schema(member),
            })
    return tools


def call_tool(rpa, tool_name: str, args: dict) -> str:
    """Dispatch a tool call into the RPA instance and return a string result.

    Must be invoked on the Qt main thread (RPA is not thread-safe). Errors are
    converted to strings; the caller is responsible for marking the
    ``tool_result`` block with ``is_error=True``.
    """
    if "__" not in tool_name:
        raise ValueError(f"malformed tool name: {tool_name!r}")
    module_name, method_name = tool_name.split("__", 1)
    if module_name not in _RPA_MODULES:
        raise ValueError(f"unknown module: {module_name!r}")

    module = getattr(rpa, module_name)
    method = getattr(module, method_name)
    result = method(**(args or {}))
    text = repr(result)
    if len(text) > _MAX_RESULT_CHARS:
        text = text[:_MAX_RESULT_CHARS] + f"\n...[truncated, total {len(text)} chars]"
    return text
