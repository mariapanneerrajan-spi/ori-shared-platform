"""
CLI arg declarations for the Session Auto Saver plugin.

This file is imported by launch_app.py BEFORE rv.exe boots, so it must
stay import-light: argparse only. No Qt, no rpa, no rpa_app.skin imports.
"""
import argparse


def add_cmd_line_args(parser: argparse.ArgumentParser) -> None:
    group = parser.add_argument_group("Annotations")
    group.add_argument(
        '--pc', '--pencolor',
        action='store',
        type=float,
        nargs=3,
        metavar=('RED', 'GREEN', 'BLUE'),
        dest='pencolor',
        help='Specify annotation pen color as RGB of [0.0 - 1.0]'
    )
