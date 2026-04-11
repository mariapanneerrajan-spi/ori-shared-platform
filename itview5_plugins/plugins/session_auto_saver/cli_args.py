"""
CLI arg declarations for the Session Auto Saver plugin.

This file is imported by launch_itview.py BEFORE rv.exe boots, so it must
stay import-light: argparse only. No Qt, no rpa, no itview.skin imports.
"""
import argparse


def add_cmd_line_args(parser: argparse.ArgumentParser) -> None:
    group = parser.add_argument_group("Session Auto Saver")
    group.add_argument(
        "--na", "--noautosave",
        action="store_true",
        dest="no_session_autosave",
        help="Do not show autosave dialog")
