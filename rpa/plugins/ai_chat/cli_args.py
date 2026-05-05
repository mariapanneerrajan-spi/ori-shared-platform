"""
CLI arg declarations for the AI Chat plugin.

Imported by launch_app.py BEFORE rv.exe boots, so it must stay import-light:
argparse only. No Qt, no rpa, no anthropic imports here.
"""
import argparse


def add_cmd_line_args(parser: argparse.ArgumentParser) -> None:
    group = parser.add_argument_group("AI Chat")
    group.add_argument(
        '--anthropic-api-key',
        action='store',
        type=str,
        default=None,
        dest='anthropic_api_key',
        help='Anthropic API key for the AI Chat plugin. '
             'Falls back to $ANTHROPIC_API_KEY, then to QSettings.'
    )
    group.add_argument(
        '--ai-model',
        action='store',
        type=str,
        default=None,
        dest='ai_model',
        help='Claude model id (e.g. claude-sonnet-4-6). '
             'Falls back to QSettings, then to a built-in default.'
    )
