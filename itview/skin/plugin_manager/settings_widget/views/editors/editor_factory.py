"""
EditorFactory - Factory for creating appropriate editor widgets.

Uses the Factory Pattern to create editor instances based on setting type.
"""

from typing import Dict, Optional, Type

from itview.skin.plugin_manager.settings_widget.qt_compat import QWidget
from itview.skin.plugin_manager.settings_widget.models.setting_item import SettingItem, SettingType
from itview.skin.plugin_manager.settings_widget.views.editors.base_editor import BaseEditor
from itview.skin.plugin_manager.settings_widget.views.editors.boolean_editor import BooleanEditor
from itview.skin.plugin_manager.settings_widget.views.editors.string_editor import StringEditor
from itview.skin.plugin_manager.settings_widget.views.editors.number_editor import IntegerEditor, NumberEditor
from itview.skin.plugin_manager.settings_widget.views.editors.enum_editor import EnumEditor
from itview.skin.plugin_manager.settings_widget.views.editors.array_editor import ArrayEditor
from itview.skin.plugin_manager.settings_widget.views.editors.path_editor import FilePathEditor, DirPathEditor
from itview.skin.plugin_manager.settings_widget.views.editors.color_editor import ColorEditor


class EditorFactory:
    """
    Factory for creating setting editor widgets.

    Maps setting types to their corresponding editor classes and
    provides a unified interface for editor creation.

    Follows the Factory Pattern for extensibility - new editor types
    can be registered at runtime.
    """

    # Default mapping of setting types to editor classes
    _editor_map: Dict[SettingType, Type[BaseEditor]] = {
        SettingType.BOOLEAN: BooleanEditor,
        SettingType.STRING: StringEditor,
        SettingType.INTEGER: IntegerEditor,
        SettingType.NUMBER: NumberEditor,
        SettingType.ENUM: EnumEditor,
        SettingType.ARRAY: ArrayEditor,
        SettingType.FILE_PATH: FilePathEditor,
        SettingType.DIR_PATH: DirPathEditor,
        SettingType.COLOR: ColorEditor,
    }

    @classmethod
    def create_editor(
        cls,
        setting: SettingItem,
        parent: Optional[QWidget] = None
    ) -> BaseEditor:
        """
        Creates an appropriate editor widget for the given setting.

        Args:
            setting: The setting item to create an editor for
            parent: Optional parent widget

        Returns:
            An editor widget instance appropriate for the setting type

        Raises:
            ValueError: If no editor is registered for the setting type
        """
        editor_class = cls._editor_map.get(setting.setting_type)

        if editor_class is None:
            # Fall back to string editor for unknown types
            editor_class = StringEditor

        return editor_class(setting, parent)

    @classmethod
    def register_editor(
        cls,
        setting_type: SettingType,
        editor_class: Type[BaseEditor]
    ) -> None:
        """
        Registers a custom editor class for a setting type.

        Allows extending the factory with new editor types.

        Args:
            setting_type: The setting type to register for
            editor_class: The editor class to use
        """
        cls._editor_map[setting_type] = editor_class

    @classmethod
    def get_supported_types(cls) -> list:
        """
        Returns list of setting types that have registered editors.

        Returns:
            List of supported SettingType values
        """
        return list(cls._editor_map.keys())
