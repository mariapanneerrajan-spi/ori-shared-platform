"""
Shared plugin-config parsing used by both the pre-rv launcher
(launch_itview.py) and the in-rvpkg Controller.

Must stay import-light: only `os` / `pathlib`. No Qt, no rpa, no itview.skin
imports - the launcher runs this before a QApplication exists.
"""
import os
from typing import List


def read_plugin_paths(cfg_path: str) -> List[str]:
    """
    Parse a plugin config file and return the raw (unresolved) plugin paths.

    The config format is: one path per line, optional trailing comma,
    `#` starts a comment, blank lines ignored.
    """
    plugin_paths: List[str] = []
    with open(cfg_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            plugin_paths.append(line.rstrip(","))
    return plugin_paths


def resolve_plugin_folders(cfg_path: str) -> List[str]:
    """
    Parse a plugin config file and return absolute plugin folder paths.

    Relative paths are resolved against the config file's own directory -
    matches the semantics used by Controller.__get_plugin_paths.
    Non-existent configs return an empty list (the Controller logs these;
    the launcher can't log to the same place, so it stays silent).
    """
    if not os.path.isfile(cfg_path):
        return []

    config_dir = os.path.abspath(os.path.dirname(cfg_path))
    folders: List[str] = []
    for path in read_plugin_paths(cfg_path):
        abs_path = path if os.path.isabs(path) else os.path.join(config_dir, path)
        folders.append(abs_path.rstrip(os.sep))
    return folders
