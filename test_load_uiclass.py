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

class Color(QWidget):
    
    def __init__(self, color, *args, **kwargs):
        super(Color, self).__init__(*args, **kwargs)
        self.setAutoFillBackground(True)
        
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(color))
        self.setPalette(palette)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Set MainWindow setting
        self.setWindowTitle('test')
        # self.setMinimumSize(640, 320)

        # Create QLabel for showing and drawing image.
        self.img = QPixmap()
        self.canvas = Canvas(parent=self)
        # self.canvas.setSizePolicy(QSizePolicy.Expanding, 
        #     QSizePolicy.Expanding)

        # Create button to load image
        self.loadImage_btn = QPushButton('Load image')
        self.loadImage_btn.clicked.connect(self.loadImageSlot)

        self.zoominImage_btn = QPushButton('Zoom in')
        self.zoominImage_btn.clicked.connect(self.zoominImageSlot)
        self.zoomoutImage_btn = QPushButton('Zoom out')
        self.zoomoutImage_btn.clicked.connect(self.zoomoutImageSlot)

        # TODO: Create scrollArea
        scroll = QScrollArea()
        scroll.setWidget(self.canvas)
        scroll.setWidgetResizable(True)
        self.scrollArea = scroll

        # Set layout
        layout = QVBoxLayout()
        # layout.addWidget(self.canvas)
        layout.addWidget(self.scrollArea)
        # layout.addWidget(self.scrollBars)
        layout.addWidget(self.loadImage_btn)
        layout.addWidget(self.zoominImage_btn)
        layout.addWidget(self.zoomoutImage_btn)

        windowContainer = QWidget()
        windowContainer.setLayout(layout)
        self.setCentralWidget(windowContainer)

    # TODO: canvas zoomin zoomout slot
    def zoominImageSlot(self):
        print('zoom')
        value = self.canvas.scale
        value += 0.1
        self.canvas.zoom(value)
        canvas_position = self.canvas.geometry()
        print('Resiing... Canvas size: {}'.format(canvas_position))

    def zoomoutImageSlot(self):
        print('zoom')
        value = self.canvas.scale
        value -= 0.1
        self.canvas.zoom(value)
        canvas_position = self.canvas.geometry()
        print('Resiing... Canvas size: {}'.format(canvas_position))

    def zoomRequest(self, delta):
        print('here')
        self.img = self.img.scaled(self.img.width() - 5, self.img.height() - 5, Qt.SmoothTransformation)
        self.canvas.setPixmap(self.img)
    
    # TODO: MainWindow resize event
    def resizeEvent(self, event):
        # self.canvas.setMinimumSize(self.scrollArea.width(), self.scrollArea.height())

        canvas_position = self.canvas.geometry()
        print('Resiing... Canvas size: {}'.format(canvas_position))
        scrollArea_position = self.scrollArea.geometry()
        print('Resiing... ScrollArea size: {}'.format(scrollArea_position))

    def loadImageSlot(self):
        file, _ = QFileDialog.getOpenFileName(self, "Open Image", 
            PATH_FILE, "Image Files (*.png *.jpg *.bmp *.tiff)")
        print('file path: {}'.format(file))

        # Show image on QLabel
        # self.img = QPixmap(file)
        # self.canvas.setPixmap(self.img)
        # self.canvas.setScaledContents(True)
        
        # TODO: Show image on QWidget
        self.img = QPixmap(file)
        if self.img:
            self.canvas.setMinimumSize(self.canvas.width(), self.canvas.height())
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

    # values = ['1', '2', '3',
    #           '4', '5', '6',
    #           '7', '8', '9']

    # positions = [ (r, c) for r in range(3) for c in range(3) ]
    # print(*positions)