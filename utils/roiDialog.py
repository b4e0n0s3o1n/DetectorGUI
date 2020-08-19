from PySide2.QtGui import *
from PySide2.QtCore import *
from PySide2.QtWidgets import *

class ROIDialog(QDialog):
    def __init__(self, text='Enter description of ROI', parent=None):
        super().__init__(parent)
        self.setWindowTitle(text)
        self.resize(QSize(325, 86))
        
        # Create textbox.
        self.edit = QLineEdit()
        self.edit.setText(text)

        # Create OK & Canncel button
        self.buttonBox = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal, self)
        self.buttonBox.button(QDialogButtonBox.Ok).setIcon(
            QIcon('./resources/icons/done.png'))
        self.buttonBox.button(QDialogButtonBox.Cancel).setIcon(
            QIcon('./resources/icons/cancel.png'))

        # Connect slot of button.
        self.buttonBox.accepted.connect(self.validate)
        self.buttonBox.rejected.connect(self.reject)

        # Set layout
        layout = QVBoxLayout()
        layout.addWidget(self.edit)
        layout.addWidget(self.buttonBox)
        self.setLayout(layout)

    def validate(self):
        """Validate entered text."""
        if self.edit.text().strip():
            self.accept()

    def popUp(self, text=''):
        """Popup dialog to enter description of ROI."""
        self.edit.setText(text)
        self.edit.setSelection(0, len(text))
        self.edit.setFocus(Qt.PopupFocusReason)
        return self.edit.text() if self.exec_() else None