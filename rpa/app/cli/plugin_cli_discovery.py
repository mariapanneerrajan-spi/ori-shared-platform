"""
Qt-free discovery of per-plugin `cli_args.py` modules.

A plugin folder may optionally contain a `cli_args.py` with a module-level
`add_cmd_line_args(parser)` function. The launcher imports these *before*
rv.exe boots (no QApplication, no rv module), builds a single ArgumentParser
from them, parses sys.argv, and serializes the resulting Namespace into an
env var for the in-rvpkg Controller to read back.

This module must stay import-light: only stdlib. No Qt, no rpa, no
rpa_app.skin imports.
"""
import argparse
import importlib.util
import json
import os
import sys
from types import ModuleType
from typing import List, Tuple


CLI_ARGS_FILENAME = "cli_args.py"
_IMPORT_NAMESPACE = "rpa_app_cli_args"


def discover_cli_modules(
    plugin_folders: List[str]) -> List[Tuple[str, ModuleType]]:
    """
    For each plugin folder, probe for `cli_args.py` and import it under a
    private namespace so it cannot clash with the real plugin module that
    gets imported later inside the rvpkg.

    Folders without a `cli_args.py` are skipped silently. A `cli_args.py`
    whose import raises is skipped with a warning to stderr - the launcher
    should not abort the whole app because one plugin has a broken CLI
    module.
    """
    modules: List[Tuple[str, ModuleType]] = []
    seen_plugin_names = set()

    for folder in plugin_folders:
        cli_path = os.path.join(folder, CLI_ARGS_FILENAME)
        if not os.path.isfile(cli_path):
            continue

        plugin_name = os.path.basename(folder.rstrip(os.sep))
        if plugin_name in seen_plugin_names:
            # The Controller's ImportPathEnforcer also dedupes by plugin name
            # (first-wins); mirror that here so both phases agree on the
            # plugin set.
            continue
        seen_plugin_names.add(plugin_name)

        module_name = f"{_IMPORT_NAMESPACE}.{plugin_name}"
        try:
            spec = importlib.util.spec_from_file_location(module_name, cli_path)
            if spec is None or spec.loader is None:
                print(
                    f"[rpa_app cli] Could not build import spec for {cli_path}",
                    file=sys.stderr)
                continue
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        except Exception as exc:
            print(
                f"[rpa_app cli] Skipping {cli_path}: import failed: {exc}",
                file=sys.stderr)
            continue

        if not hasattr(module, "add_cmd_line_args"):
            print(
                f"[rpa_app cli] {cli_path} has no add_cmd_line_args(parser) "
                f"function - skipping",
                file=sys.stderr)
            continue

        modules.append((plugin_name, module))

    return modules


def build_parser(
    plugin_cli_modules: List[Tuple[str, ModuleType]],
    prog: str = "rpa_app") -> argparse.ArgumentParser:
    """
    Create the top-level ArgumentParser and let each plugin's cli_args
    module register its flags. Dest-name collisions raise argparse.ArgumentError
    at registration time, which the launcher surfaces as a clean error.
    """
    parser = argparse.ArgumentParser(
        prog=prog,
        description="App command line arguments")

    for plugin_name, module in plugin_cli_modules:
        try:
            module.add_cmd_line_args(parser)
        except argparse.ArgumentError as exc:
            # Most likely a dest collision across plugins. Re-raise with
            # context so the user sees which plugin caused it.
            raise argparse.ArgumentError(
                exc.argument,
                f"in plugin '{plugin_name}': {exc.message}") from exc

    return parser


def parse_and_serialize(
    parser: argparse.ArgumentParser, argv: List[str]) -> str:
    """
    Parse argv with the given parser and return a JSON string of the
    resulting Namespace. argparse handles --help / errors by writing to
    the terminal and calling sys.exit, which is exactly what we want:
    the launcher inherits that behavior for free.

    Any Namespace value that isn't JSON-serializable is a plugin-author
    bug - surface it with a clear message so they know which arg to fix.
    """
    namespace = parser.parse_args(argv)
    try:
        return json.dumps(vars(namespace))
    except TypeError as exc:
        raise SystemExit(
            f"[rpa_app cli] A plugin CLI argument value is not JSON-"
            f"serializable: {exc}. Use only primitive types (str, int, "
            f"float, bool, None, list, dict) in your cli_args.py.") from exc
