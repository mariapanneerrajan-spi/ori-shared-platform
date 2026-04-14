"""
PySide2/PySide6 Compatibility Shim.

This module provides a unified import interface for Qt components,
automatically selecting PySide6 if available, falling back to PySide2.

Usage:
    from itview.skin.plugin_manager.settings_widget.qt_compat import QWidget, Signal, Qt
"""

# Attempt PySide6 first, fallback to PySide2
try:
    from PySide6.QtWidgets import (
        QWidget,
        QMainWindow,
        QVBoxLayout,
        QHBoxLayout,
        QFormLayout,
        QGridLayout,
        QLineEdit,
        QCheckBox,
        QComboBox,
        QSpinBox,
        QDoubleSpinBox,
        QScrollArea,
        QTreeWidget,
        QTreeWidgetItem,
        QGroupBox,
        QPushButton,
        QLabel,
        QColorDialog,
        QFileDialog,
        QFrame,
        QSizePolicy,
        QSplitter,
        QStackedWidget,
        QListWidget,
        QListWidgetItem,
        QApplication,
        QStyle,
        QHeaderView,
        QMessageBox,
        QStatusBar,
    )
    from PySide6.QtCore import (
        Qt,
        Signal,
        Slot,
        QTimer,
        QSize,
        QObject,
        Property,
    )
    from PySide6.QtGui import (
        QColor,
        QIcon,
        QFont,
        QPalette,
        QPixmap,
    )
    PYSIDE_VERSION = 6

except ImportError:
    from PySide2.QtWidgets import (
        QWidget,
        QMainWindow,
        QVBoxLayout,
        QHBoxLayout,
        QFormLayout,
        QGridLayout,
        QLineEdit,
        QCheckBox,
        QComboBox,
        QSpinBox,
        QDoubleSpinBox,
        QScrollArea,
        QTreeWidget,
        QTreeWidgetItem,
        QGroupBox,
        QPushButton,
        QLabel,
        QColorDialog,
        QFileDialog,
        QFrame,
        QSizePolicy,
        QSplitter,
        QStackedWidget,
        QListWidget,
        QListWidgetItem,
        QApplication,
        QStyle,
        QHeaderView,
        QMessageBox,
        QStatusBar,
    )
    from PySide2.QtCore import (
        Qt,
        Signal,
        Slot,
        QTimer,
        QSize,
        QObject,
        Property,
    )
    from PySide2.QtGui import (
        QColor,
        QIcon,
        QFont,
        QPalette,
        QPixmap,
    )
    PYSIDE_VERSION = 2


def get_pyside_version() -> int:
    """Returns the PySide version being used (2 or 6)."""
    return PYSIDE_VERSION
