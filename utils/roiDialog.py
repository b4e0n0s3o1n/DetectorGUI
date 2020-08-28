from PySide2.QtGui import *
from PySide2.QtCore import *
from PySide2.QtWidgets import *

class ROIDialog(QDialog):
    def __init__(self, text='Enter description of ROI', parent=None):
        super().__init__(parent)
        self.setWindowTitle(text)
        self.resize(QSize(325, 86))

        # Create label.
        self.machineName_lb = QLabel('machineName')
        self.frameName_lb = QLabel('frameName')
        self.roiName_lb = QLabel('roiName')
        ## Set minimum width of label.
        self.machineName_lb.setFixedWidth(80)
        self.frameName_lb.setFixedWidth(80)
        self.roiName_lb.setFixedWidth(80)
        
        # Create textbox.
        self.machineName = QLineEdit()
        self.machineName.setText(text)
        self.frameName = QLineEdit()
        self.frameName.setText(text)
        self.roiName = QLineEdit()
        self.roiName.setText(text)

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
        ## Set machineName layout
        machineLayout = QHBoxLayout()
        machineLayout.addWidget(self.machineName_lb)
        machineLayout.addWidget(self.machineName)
        machineWidget = QWidget()
        machineWidget.setLayout(machineLayout)
        ## Set frameName layout
        frameLayout = QHBoxLayout()
        frameLayout.addWidget(self.frameName_lb)
        frameLayout.addWidget(self.frameName)
        frameWidget = QWidget()
        frameWidget.setLayout(frameLayout)
        ## Set roiName layout
        roiLayout = QHBoxLayout()
        roiLayout.addWidget(self.roiName_lb)
        roiLayout.addWidget(self.roiName)
        roiWidget = QWidget()
        roiWidget.setLayout(roiLayout)

        layout = QVBoxLayout()
        layout.addWidget(machineWidget)
        layout.addWidget(frameWidget)
        layout.addWidget(roiWidget)
        layout.addWidget(self.buttonBox)
        self.setLayout(layout)

    def validate(self):
        """Validate entered text."""
        if self.machineName.text().strip() and \
            self.frameName.text().strip() and \
            self.roiName.text().strip():
            self.accept()

    def popUp(self, text=''):
        """Popup dialog to enter description of ROI."""
        self.machineName.setText(text)
        self.frameName.setText(text)
        self.roiName.setText(text)
        self.machineName.setSelection(0, len(text))
        self.frameName.setSelection(0, len(text))
        self.roiName.setSelection(0, len(text))
        self.machineName.setFocus(Qt.PopupFocusReason)

        return (
            self.machineName.text(), 
            self.frameName.text(), 
            self.roiName.text()
            ) if self.exec_() else (None, None, None)