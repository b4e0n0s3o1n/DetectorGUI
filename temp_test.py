from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
import sys 

class Main(QMainWindow): 
    def __init__(self, parent = None): 
        super(Main, self).__init__(parent) 

        # main button 
        self.addButton = QPushButton('button to add other widgets') 
        self.addButton.clicked.connect(self.addWidget) 

        # scroll area widget contents - layout 
        self.scrollLayout = QFormLayout() 

        # scroll area widget contents 
        self.scrollWidget = QWidget() 
        self.scrollWidget.setLayout(self.scrollLayout) 

        # scroll area 
        self.scrollArea = QScrollArea() 
        self.scrollArea.setWidgetResizable(True) 
        self.scrollArea.setWidget(self.scrollWidget) 

        # main layout 
        self.mainLayout = QVBoxLayout() 

        # add all main to the main vLayout 
        self.mainLayout.addWidget(self.addButton) 
        self.mainLayout.addWidget(self.scrollArea) 

        # central widget 
        self.centralWidget = QWidget() 
        self.centralWidget.setLayout(self.mainLayout) 

        # set central widget 
        self.setCentralWidget(self.centralWidget) 

        self.img = QPixmap()

    def addWidget(self): 
        self.scrollLayout.addRow(Test())
        print(self.scrollWidget.geometry())

    def resizeEvent(self, event):
        window_position = self.scrollWidget.geometry()
        print('resizing...: {}'.format(window_position))


class Test(QWidget): 
    def __init__(self, parent=None): 
        super(Test, self).__init__(parent) 

        self.pushButton = QPushButton('I am in Test widget') 

        layout = QHBoxLayout() 
        layout.addWidget(self.pushButton) 
        self.setLayout(layout) 


app = QApplication(sys.argv) 
myWidget = Main() 
myWidget.show() 
app.exec_() 