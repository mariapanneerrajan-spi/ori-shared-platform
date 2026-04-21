"""
Deprecated: use rpa.utils.qt instead.

Kept as a thin re-export so existing callers keep working; new code should
import submodules directly, e.g.:
    from rpa.utils.qt import QtCore, QtGui, QtWidgets
"""
from rpa.utils.qt import (
    QtCore,
    QtGui,
    QtWidgets,
    PYSIDE_VERSION,
    QT_BINDING,
    get_pyside_version,
)

# Preserve the original flat symbol surface used by existing callers.
from rpa.utils.qt.QtWidgets import (
    QWidget, QMainWindow, QVBoxLayout, QHBoxLayout, QFormLayout, QGridLayout,
    QLineEdit, QCheckBox, QComboBox, QSpinBox, QDoubleSpinBox, QScrollArea,
    QTreeWidget, QTreeWidgetItem, QGroupBox, QPushButton, QLabel, QColorDialog,
    QFileDialog, QFrame, QSizePolicy, QSplitter, QStackedWidget, QListWidget,
    QListWidgetItem, QApplication, QStyle, QHeaderView, QMessageBox, QStatusBar,
)
from rpa.utils.qt.QtCore import (
    Qt, Signal, Slot, QTimer, QSize, QObject, Property,
)
from rpa.utils.qt.QtGui import (
    QColor, QIcon, QFont, QPalette, QPixmap,
)
