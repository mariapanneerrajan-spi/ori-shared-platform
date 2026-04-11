#!/usr/bin/env python
"""
Pre-rv launcher for Itview5.

Runs BEFORE rv.exe boots so plugin-owned `--help` and CLI errors can print
to the terminal without starting a Qt GUI. Discovers plugin `cli_args.py`
modules, builds a single argparse parser, parses sys.argv[1:], stashes the
result in an env var, and then execs rv.exe with a CLEAN argv so OpenRV's
own CLI is fully overridden.

Invoked from the shell launchers (launch_itview.bat / launch_itview /
itview / itview.bat) which set up RV_HOME, RV_SUPPORT_PATH, PYTHONPATH,
and ITVIEW5_CORE_PLUGINS_CONFIG before running this script.
"""
import os
import sys

# This file lives inside the `itview` package. When invoked as
# `python -m itview.launch_itview ...` (how the shell launchers call it)
# the package is already importable. When someone runs the file directly
# from an IDE, make the parent directory importable so `itview.*` imports
# still resolve.
_THIS_FILE = os.path.abspath(__file__)
_PKG_PARENT = os.path.dirname(os.path.dirname(_THIS_FILE))
if _PKG_PARENT not in sys.path:
    sys.path.insert(0, _PKG_PARENT)

from itview.cli.env_keys import ITVIEW5_CLI_ARGS_JSON
from itview.cli.plugin_cli_discovery import (
    discover_cli_modules, build_parser, parse_and_serialize)
from itview.skin.plugin_manager.plugin_config_reader import resolve_plugin_folders


def _get_plugin_config_paths():
    """
    Mirror of itview.plugin_path_configs.get() but without pulling in the
    Qt-importing `model.ConfigPath` dataclass. We only need the file paths
    here; the launcher is deliberately Qt-free.
    """
    paths = []
    config_name = "itview5_plugins.cfg"

    # Current Directory
    cwd_cfg = os.path.join(os.getcwd(), config_name)
    if os.path.isfile(cwd_cfg):
        paths.append(cwd_cfg)

    # Home Directory
    home_cfg = os.path.join(os.path.expanduser("~"), ".itview", config_name)
    if os.path.isfile(home_cfg):
        paths.append(home_cfg)

    # Core Plugins (set by the shell launcher)
    core_cfg = os.environ.get("ITVIEW5_CORE_PLUGINS_CONFIG")
    if core_cfg and os.path.isfile(core_cfg):
        paths.append(core_cfg)

    return paths


def _resolve_rv_executable():
    """Return the absolute path to rv.exe / rv, or exit with an error."""
    rv_home = os.environ.get("RV_HOME")
    if not rv_home:
        print("ERROR: RV_HOME is not set.", file=sys.stderr)
        print("Set it to your OpenRV installation directory.", file=sys.stderr)
        sys.exit(1)

    if sys.platform == "win32":
        rv_exe = os.path.join(rv_home, "bin", "rv.exe")
    else:
        rv_exe = os.path.join(rv_home, "bin", "rv")

    if not os.path.isfile(rv_exe):
        print(f"ERROR: rv executable not found at {rv_exe}", file=sys.stderr)
        sys.exit(1)

    return rv_exe


def main():
    print("Itview5 launcher starting...")
    rv_exe = _resolve_rv_executable()

    # Walk all plugin configs and collect every plugin folder, preserving
    # discovery order so the first config wins on duplicate plugin names
    # (matches Controller.ImportPathEnforcer semantics).
    plugin_folders = []
    for cfg_path in _get_plugin_config_paths():
        plugin_folders.extend(resolve_plugin_folders(cfg_path))

    # Build the combined parser from every plugin's cli_args.py.
    cli_modules = discover_cli_modules(plugin_folders)
    parser = build_parser(cli_modules)

    # parse_args() handles --help / errors with its own sys.exit, which
    # we deliberately inherit: the terminal sees help/errors before rv
    # ever starts.
    args_json = parse_and_serialize(parser, sys.argv[1:])

    # Hand the parsed values off to the in-rvpkg Controller.
    os.environ[ITVIEW5_CLI_ARGS_JSON] = args_json

    # Launch rv with a CLEAN argv - no passthrough. OpenRV's own CLI is
    # now fully replaced by itview's CLI. On Windows os.execv replaces the
    # current process so rv.exe inherits our env (including the args JSON).
    os.execv(rv_exe, [rv_exe])


if __name__ == "__main__":
    main()
