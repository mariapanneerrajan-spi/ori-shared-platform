"""
Editor widgets package.

Contains editor widgets for each setting type, all inheriting from BaseEditor.
The EditorFactory creates appropriate editors based on setting type.
"""

from rpa.app.skin.plugin_manager.settings_widget.views.editors.base_editor import BaseEditor
from rpa.app.skin.plugin_manager.settings_widget.views.editors.boolean_editor import BooleanEditor
from rpa.app.skin.plugin_manager.settings_widget.views.editors.string_editor import StringEditor
from rpa.app.skin.plugin_manager.settings_widget.views.editors.number_editor import IntegerEditor, NumberEditor
from rpa.app.skin.plugin_manager.settings_widget.views.editors.enum_editor import EnumEditor
from rpa.app.skin.plugin_manager.settings_widget.views.editors.array_editor import ArrayEditor
from rpa.app.skin.plugin_manager.settings_widget.views.editors.path_editor import FilePathEditor, DirPathEditor
from rpa.app.skin.plugin_manager.settings_widget.views.editors.color_editor import ColorEditor
from rpa.app.skin.plugin_manager.settings_widget.views.editors.editor_factory import EditorFactory

__all__ = [
    "BaseEditor",
    "BooleanEditor",
    "StringEditor",
    "IntegerEditor",
    "NumberEditor",
    "EnumEditor",
    "ArrayEditor",
    "FilePathEditor",
    "DirPathEditor",
    "ColorEditor",
    "EditorFactory",
]
