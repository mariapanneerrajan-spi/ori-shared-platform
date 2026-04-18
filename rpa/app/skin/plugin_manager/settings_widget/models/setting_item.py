"""
SettingItem - Data model for individual settings.

Each setting has a type, default value, constraints, and metadata
for display in the UI.
"""

from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Union
from dataclasses import dataclass, field


class SettingType(Enum):
    """
    Enumeration of supported setting types.

    Each type maps to a specific editor widget in the view layer.
    """
    BOOLEAN = auto()      # Checkbox
    STRING = auto()       # Text input
    INTEGER = auto()      # Integer spinbox
    NUMBER = auto()       # Decimal spinbox
    ENUM = auto()         # Dropdown selection
    ARRAY = auto()        # List of items
    FILE_PATH = auto()    # File picker
    DIR_PATH = auto()     # Directory picker
    COLOR = auto()        # Color picker
    KEY_BINDING = auto()  # Keyboard shortcut


@dataclass
class SettingItem:
    """
    Represents a single configurable setting.

    Attributes:
        id: Unique identifier within namespace (e.g., "enableFeature")
        setting_type: Type of the setting (determines editor widget)
        default: Default value for the setting
        title: Human-readable title for display
        description: Detailed description shown below the setting
        namespace: Plugin namespace (e.g., "myPlugin")
        category: Category for grouping in sidebar
        value: Current value (if different from default)
        options: For ENUM type - list of valid options
        minimum: For numeric types - minimum allowed value
        maximum: For numeric types - maximum allowed value
        step: For numeric types - increment step
        placeholder: Placeholder text for string inputs
        file_filter: For FILE_PATH - file type filter string
        validators: List of validation functions
        depends_on: ID of setting this depends on for visibility
        tags: Search tags for improved discoverability
    """
    id: str
    setting_type: SettingType
    default: Any
    title: str
    description: str = ""
    namespace: str = ""
    category: str = "General"
    value: Any = None
    options: List[Union[str, Dict[str, str]]] = field(default_factory=list)
    minimum: Optional[Union[int, float]] = None
    maximum: Optional[Union[int, float]] = None
    step: Union[int, float] = 1
    placeholder: str = ""
    file_filter: str = "All Files (*.*)"
    validators: List[Callable[[Any], bool]] = field(default_factory=list)
    depends_on: Optional[str] = None
    tags: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Initialize value to default if not set."""
        if self.value is None:
            self.value = self.default

    @property
    def full_id(self) -> str:
        """Returns fully qualified setting ID (namespace.id)."""
        if self.namespace:
            return f"{self.namespace}.{self.id}"
        return self.id

    def get_value(self) -> Any:
        """Returns current value, falling back to default."""
        return self.value if self.value is not None else self.default

    def set_value(self, value: Any) -> bool:
        """
        Sets the setting value after validation.

        Args:
            value: New value to set

        Returns:
            True if value was set successfully, False if validation failed
        """
        if self.validate(value):
            self.value = value
            return True
        return False

    def reset_to_default(self) -> None:
        """Resets the setting to its default value."""
        self.value = self.default

    def is_modified(self) -> bool:
        """Returns True if value differs from default."""
        return self.value != self.default

    def validate(self, value: Any) -> bool:
        """
        Validates a value against type constraints and custom validators.

        Args:
            value: Value to validate

        Returns:
            True if valid, False otherwise
        """
        # Type-specific validation
        if self.setting_type == SettingType.BOOLEAN:
            if not isinstance(value, bool):
                return False

        elif self.setting_type == SettingType.INTEGER:
            if not isinstance(value, int):
                return False
            if self.minimum is not None and value < self.minimum:
                return False
            if self.maximum is not None and value > self.maximum:
                return False

        elif self.setting_type == SettingType.NUMBER:
            if not isinstance(value, (int, float)):
                return False
            if self.minimum is not None and value < self.minimum:
                return False
            if self.maximum is not None and value > self.maximum:
                return False

        elif self.setting_type == SettingType.STRING:
            if not isinstance(value, str):
                return False

        elif self.setting_type == SettingType.ENUM:
            valid_values = self._get_enum_values()
            if value not in valid_values:
                return False

        elif self.setting_type == SettingType.ARRAY:
            if not isinstance(value, list):
                return False

        # Run custom validators
        for validator in self.validators:
            if not validator(value):
                return False

        return True

    def _get_enum_values(self) -> List[str]:
        """Extracts valid enum values from options list."""
        values = []
        for option in self.options:
            if isinstance(option, dict):
                values.append(option.get("value", option.get("label", "")))
            else:
                values.append(option)
        return values

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the setting to a dictionary."""
        return {
            "id": self.id,
            "type": self.setting_type.name,
            "default": self.default,
            "value": self.value,
            "title": self.title,
            "description": self.description,
            "namespace": self.namespace,
            "category": self.category,
            "options": self.options,
            "minimum": self.minimum,
            "maximum": self.maximum,
            "step": self.step,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SettingItem":
        """
        Creates a SettingItem from a dictionary.

        Args:
            data: Dictionary with setting configuration

        Returns:
            New SettingItem instance
        """
        setting_type = data.get("type", "STRING")
        if isinstance(setting_type, str):
            setting_type = SettingType[setting_type.upper()]

        return cls(
            id=data["id"],
            setting_type=setting_type,
            default=data.get("default"),
            title=data.get("title", data["id"]),
            description=data.get("description", ""),
            namespace=data.get("namespace", ""),
            category=data.get("category", "General"),
            value=data.get("value"),
            options=data.get("options", []),
            minimum=data.get("minimum"),
            maximum=data.get("maximum"),
            step=data.get("step", 1),
            placeholder=data.get("placeholder", ""),
            file_filter=data.get("file_filter", "All Files (*.*)"),
            depends_on=data.get("depends_on"),
            tags=data.get("tags", []),
        )
