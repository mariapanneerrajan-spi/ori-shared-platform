from rpa.utils.qt import QtCore, QtWidgets


class ColorSwizzleDialog(QtWidgets.QDialog):
    """The pop-up dialog for custom channel mapping."""
    # Signal emitted whenever the channel order changes in the dialog
    order_changed = QtCore.Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Color Swizzle")
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.Tool) # Keeps it floating nicely
        
        layout = QtWidgets.QHBoxLayout(self)

        self.combos = []
        channels_labels = ["R", "G", "B", "A"]
        # Added 0 and 1 as they are standard for swizzling (e.g., R00A)
        options = ["R", "G", "B", "A", "L", "1", "0"]

        # Create the R, G, B, A columns
        for label_text in channels_labels:
            vbox = QtWidgets.QVBoxLayout()
            lbl = QtWidgets.QLabel(label_text)
            lbl.setAlignment(QtCore.Qt.AlignCenter)
            
            combo = QtWidgets.QComboBox()
            combo.addItems(options)
            combo.currentTextChanged.connect(self._on_combo_changed)
            self.combos.append(combo)

            vbox.addWidget(lbl)
            vbox.addWidget(combo)
            layout.addLayout(vbox)

        # Create the Reset button
        self.reset_btn = QtWidgets.QPushButton("Reset")
        self.reset_btn.clicked.connect(self.reset_to_default)
        layout.addWidget(self.reset_btn)

    def set_order(self, order_list):
        """Silently update the comboboxes without triggering signals."""
        for combo, val in zip(self.combos, order_list):
            combo.blockSignals(True)
            combo.setCurrentText(val)
            combo.blockSignals(False)

    def _on_combo_changed(self):
        new_order = [combo.currentText() for combo in self.combos]
        self.order_changed.emit(new_order)

    def reset_to_default(self):
        self.set_order(["R", "G", "B", "A"])
        self._on_combo_changed()



