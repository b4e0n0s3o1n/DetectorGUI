import os
import sys
import random
import cv2
from PySide2 import QtCore, QtWidgets, QtGui
from PySide2.QtCore import Qt, QMetaObject, QFile, QPoint
from PySide2.QtWidgets import QFileDialog
from PySide2.QtUiTools import QUiLoader
from PySide2.QtGui import QPixmap, QPainter
# from PyQt5.QtGui import *
# sys.path.append("..")
# from canvas import Canvas

QtCore.QCoreApplication.addLibraryPath(os.path.join(os.path.dirname(QtCore.__file__), "plugins"))
PATH_FILE = os.path.dirname(os.path.abspath(__file__))

# sample class
class MyWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.hello = ['1', '2', '3', '4']

        self.button = QtWidgets.QPushButton('Click me!')
        self.text = QtWidgets.QLabel('Hello workd!')
        self.text.setAlignment(QtCore.Qt.AlignCenter)

        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addWidget(self.text)
        self.layout.addWidget(self.button)
        self.setLayout(self.layout)

        self.button.clicked.connect(self.magic)

    def magic(self):
        self.text.setText(random.choice(self.hello))

class UiLoader(QUiLoader):
    def __init__(self, baseinstance, customWidgets=None):
        QUiLoader.__init__(self, baseinstance)
        self.baseinstance = baseinstance
        self.customWidgets = customWidgets

    def createWidget(self, class_name, parent=None, name=''):
        if parent is None and self.baseinstance:
            return self.baseinstance

        else:
            if class_name in self.availableWidgets():
                widget = QUiLoader.createWidget(self, class_name, parent, name)
            
            else:
                try:
                    widget = self.customWidgets[class_name](parent)

                except (TypeError, KeyError) as e:
                    raise Exception('No custom widget ' + class_name + 'found in custimWidgets param of UiLoader __init__.')
            
            if self.baseinstance:
                setattr(self.baseinstance, name, widget)
            
            return widget

def loadUi(uifile, baseinstance=None, customWidgets=None, workingDirectory=None):
    loader = UiLoader(baseinstance, customWidgets)

    if workingDirectory is not None:
        loader.setWorkingDirectory(workingDirectory)

    widget = loader.load(uifile)
    QMetaObject.connectSlotsByName(widget)
    return widget

class testWidget(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        # super().__init__()
        # ui_file = QFile('mainwindow.ui')
        # ui_file.open(QFile.ReadOnly)
        # loader = QUiLoader()
        # self.window = loader.load(ui_file)
        # self.window.show()

        QtWidgets.QMainWindow.__init__(self, parent)
        loadUi('mainwindow.ui', self)

        # self.canvas = Canvas(parent=self)
        # self.canvas.show()

        # set label
        # self.label = self.window.label
        # self.label.setFrameShape(QtWidgets.QFrame.Box)
        # self.label.setFrameShadow(QtWidgets.QFrame.Raised)
        # self.label.setLineWidth(10)

        # set button connect
        # self.button = self.window.pushButton
        self.pushButton.clicked.connect(self.button_press)

        # set draw and image
        self._painter = QPainter()
        self.img = QPixmap()

        # set point
        self.begin_point, self.end_point = QPoint(), QPoint()
        self.setMouseTracking(True)

    def button_press(self):
        # open file
        file, _ = QFileDialog.getOpenFileName(self, "Open Image", PATH_FILE, "Image Files (*.png *.jpg *.bmp *.tiff)")
        print('file path: {}'.format(file))

        # show image
        # self.img = QPixmap(file)
        # self.label.setPixmap(self.img)
        # self.label.setScaledContents(True)

    def paintEvent(self, QPaintEvent):
        # if not self.img:
        #     return super().paintEvent(QPaintEvent)
        
        painter = self._painter
        painter.begin(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.HighQualityAntialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        if not self.img:
            print('not')
        painter.drawRect(0, 0, 400, 200)

        painter.end()

        # painter.drawLine(self.begin_point, self.end_point)
        # painter.drawRect(QtCore.QRect(self.begin_point, self.end_point))
        # self.begin_point = self.end_point

    def mousePressEvent(self, QMouseEvent):
        if QMouseEvent.button() == Qt.LeftButton:
            print('left')
            self.begin_point = QMouseEvent.pos()
            self.end_point = self.begin_point
            self.update()

    def mouseMoveEvent(self, QMouseEvent):
        if QMouseEvent.buttons() == Qt.LeftButton:
            print('move')
            self.end_point = QMouseEvent.pos()
            self.update()

if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    app.addLibraryPath(PATH_FILE)
    
    window = testWidget()
    window.show()
    sys.exit(app.exec_())