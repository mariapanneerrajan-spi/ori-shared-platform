"""Application-wide Qt styling for Itview.

The stylesheet is applied to the QApplication so it cascades to every
widget — including dock widgets and tooltips that are not children of
the main window. Call `apply_itview_styling(app)` once at startup, after
the QApplication exists, before showing the main window.
"""

from itview.skin.itview_palette import ItviewPalette


STYLESHEET = """
    QDockWidget {
        border: none;
    }
    QDockWidget::title {
        background: palette(window);
        border-bottom: 1px solid palette(dark);
        padding: 4px;
    }
    QToolBar {
        border: none;
        spacing: 2px;
    }
    QTableView, QListView, QTreeView {
        border: 1px solid palette(dark);
    }
    QSplitter::handle {
        background: palette(dark);
    }
    QHeaderView {
        background: palette(window);
        border: none;
    }
    QHeaderView::section {
        background: palette(window);
        color: palette(window-text);
        border: none;
        border-right: 1px solid palette(dark);
        border-bottom: 1px solid palette(dark);
        padding: 4px 6px;
    }
    QHeaderView::section:hover {
        background: palette(midlight);
    }
    QTableView QTableCornerButton::section {
        background: palette(window);
        border: none;
        border-right: 1px solid palette(dark);
        border-bottom: 1px solid palette(dark);
    }
    QTableView::item:selected {
        background: palette(highlight);
    }
    QHeaderView QToolButton {
        background: palette(window);
        border: none;
        padding: 2px;
    }
    QHeaderView QToolButton:hover {
        background: palette(midlight);
    }
    QMenuBar {
        background: palette(window);
        color: palette(window-text);
        border-bottom: 1px solid palette(dark);
    }
    QMenuBar::item {
        background: transparent;
        padding: 4px 8px;
    }
    QMenuBar::item:selected {
        background: palette(highlight);
    }
    QMenu {
        background: palette(window);
        color: palette(window-text);
        border: 1px solid palette(dark);
    }
    QMenu::item:selected {
        background: palette(highlight);
    }
    QTabBar::tab {
        background: palette(dark);
        color: palette(window-text);
        border: 1px solid palette(dark);
        padding: 4px 10px;
    }
    QTabBar::tab:selected {
        background: palette(window);
        border-bottom: none;
    }
    QTabBar::tab:hover {
        background: palette(midlight);
    }
    QTabWidget::pane {
        border: 1px solid palette(dark);
        background: palette(window);
    }
    QScrollBar:vertical {
        background: palette(base);
        width: 12px;
        border: none;
    }
    QScrollBar::handle:vertical {
        background: palette(midlight);
        min-height: 20px;
        border-radius: 3px;
        margin: 2px;
    }
    QScrollBar::handle:vertical:hover {
        background: palette(light);
    }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        height: 0px;
    }
    QScrollBar:horizontal {
        background: palette(base);
        height: 12px;
        border: none;
    }
    QScrollBar::handle:horizontal {
        background: palette(midlight);
        min-width: 20px;
        border-radius: 3px;
        margin: 2px;
    }
    QScrollBar::handle:horizontal:hover {
        background: palette(light);
    }
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
        width: 0px;
    }
    QToolTip {
        background: palette(base);
        color: palette(window-text);
        border: 1px solid palette(dark);
        padding: 2px;
    }
    QLineEdit {
        background: palette(base);
        color: palette(window-text);
        border: 1px solid palette(dark);
        border-radius: 2px;
        padding: 2px 4px;
    }
    QLineEdit:focus {
        border: 1px solid palette(highlight);
    }
    QComboBox {
        background: palette(base);
        color: palette(window-text);
        border: 1px solid palette(dark);
        border-radius: 2px;
        padding: 2px 6px;
    }
    QComboBox:hover {
        border: 1px solid palette(midlight);
    }
    QComboBox QAbstractItemView {
        background: palette(base);
        color: palette(window-text);
        border: 1px solid palette(dark);
        selection-background-color: palette(highlight);
    }
    QComboBox::drop-down {
        border: none;
        background: palette(window);
    }
    QSpinBox, QDoubleSpinBox {
        background: palette(base);
        color: palette(window-text);
        border: 1px solid palette(dark);
        border-radius: 2px;
        padding: 2px 4px;
    }
    QSpinBox:focus, QDoubleSpinBox:focus {
        border: 1px solid palette(highlight);
    }
    QSpinBox::up-button, QDoubleSpinBox::up-button,
    QSpinBox::down-button, QDoubleSpinBox::down-button {
        background: palette(window);
        border: none;
    }
    QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
    QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {
        background: palette(midlight);
    }
    QPushButton {
        background: palette(window);
        color: palette(window-text);
        border: 1px solid palette(dark);
        border-radius: 2px;
        padding: 4px 8px;
    }
    QPushButton:hover {
        background: palette(midlight);
    }
    QPushButton:pressed {
        background: palette(dark);
    }
    QTextEdit, QPlainTextEdit {
        background: palette(base);
        color: palette(window-text);
        border: 1px solid palette(dark);
    }
    QCheckBox::indicator {
        width: 14px;
        height: 14px;
        border: 1px solid palette(dark);
        border-radius: 2px;
        background: palette(base);
    }
    QCheckBox::indicator:checked {
        background: palette(highlight);
    }
    QSlider::groove:horizontal {
        background: palette(dark);
        height: 4px;
        border-radius: 2px;
    }
    QSlider::handle:horizontal {
        background: palette(light);
        width: 12px;
        margin: -4px 0;
        border-radius: 6px;
    }
    QSlider::handle:horizontal:hover {
        background: palette(window-text);
    }
    QSlider::groove:vertical {
        background: palette(dark);
        width: 4px;
        border-radius: 2px;
    }
    QSlider::handle:vertical {
        background: palette(light);
        height: 12px;
        margin: 0 -4px;
        border-radius: 6px;
    }
    QSlider::sub-page:horizontal {
        background: palette(highlight);
        border-radius: 2px;
    }
    QToolButton {
        background: transparent;
        border: none;
        padding: 2px;
    }
    QToolButton:hover {
        background: palette(midlight);
        border-radius: 2px;
    }
    QToolButton:pressed {
        background: palette(dark);
    }
"""


def apply_itview_styling(app):
    """Apply Itview's palette and stylesheet to the given QApplication."""
    app.setPalette(ItviewPalette())
    app.setStyleSheet(STYLESHEET)
