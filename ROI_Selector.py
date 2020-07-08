import os
import sys
import random
import cv2
from PySide2 import QtCore, QtWidgets, QtGui
from PySide2.QtCore import Qt, QMetaObject, QFile, QPoint
from PySide2.QtWidgets import *
from PySide2.QtUiTools import QUiLoader
from PySide2.QtGui import *

from utils.canvas import Canvas

QtCore.QCoreApplication.addLibraryPath(os.path.join(os.path.dirname(QtCore.__file__), "plugins"))
PATH_FILE = os.path.dirname(os.path.abspath(__file__))

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Set MainWindow setting
        self.setWindowTitle('test')
        # self.setMinimumSize(640, 320)

        # Create QLabel for showing and drawing image.
        self.img = QPixmap()
        self.canvas = Canvas(parent=self)

        # Create button
        self.loadImage_btn = QPushButton('Load image')
        self.loadImage_btn.clicked.connect(self.loadImageSlot)
        self.zoominImage_btn = QPushButton('Zoom in')
        self.zoominImage_btn.clicked.connect(self.zoomInImageSlot)
        self.zoomoutImage_btn = QPushButton('Zoom out')
        self.zoomoutImage_btn.clicked.connect(self.zoomOutImageSlot)

        # Create scroll area
        scroll = QScrollArea()
        scroll.setWidget(self.canvas)
        scroll.setWidgetResizable(True)
        self.scrollArea = scroll

        # Set layout
        layout = QVBoxLayout()
        layout.addWidget(self.scrollArea)
        layout.addWidget(self.loadImage_btn)
        layout.addWidget(self.zoominImage_btn)
        layout.addWidget(self.zoomoutImage_btn)

        # Create central widget of QMainWindow
        windowContainer = QWidget()
        windowContainer.setLayout(layout)
        self.setCentralWidget(windowContainer)

        # Set shortcuts
        QShortcut(QKeySequence.ZoomIn, self, self.zoomInImageSlot)
        QShortcut(QKeySequence.ZoomOut, self, self.zoomOutImageSlot)
        QShortcut(QKeySequence('w'), self, self.test)

    def test(self):
        print('Drawing mode...')
        self.canvas.isDrawing = True

    def zoomInImageSlot(self):
        """Slot of zooming in image."""
        value = self.canvas.scale
        value += 0.1
        self.canvas.zoom(value)
        self.canvas.adjustSize()

        canvas_position = self.canvas.geometry()
        print('Zoom in... Canvas size: {}'.format(canvas_position))

    def zoomOutImageSlot(self):
        """Slot of zooming out image."""
        value = self.canvas.scale
        value -= 0.1
        self.canvas.zoom(value)
        self.canvas.adjustSize()

        canvas_position = self.canvas.geometry()
        print('Zoom out... Canvas size: {}'.format(canvas_position))
    
    # TODO: MainWindow resize event
    def resizeEvent(self, event):
        """QMainWindow event: MainWindow resize event."""
        # self.canvas.setMinimumSize(self.scrollArea.width(), self.scrollArea.height())

    def loadImageSlot(self):
        """Slot of loading image"""
        file, _ = QFileDialog.getOpenFileName(self, "Open Image", 
            PATH_FILE, "Image Files (*.png *.jpg *.bmp *.tiff)")
        print('file path: {}'.format(file))
        
        self.img = QPixmap(file)
        if self.img:
            self.canvas.setGeometry(0, 0, self.canvas.width(), self.canvas.height())
            self.canvas.loadPixmap(self.img)

def main():
    app = QtWidgets.QApplication([])
    app.addLibraryPath(PATH_FILE)
    
    window = MainWindow()
    window.loadImageSlot()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()