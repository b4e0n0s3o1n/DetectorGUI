import os
import sys
import cv2
import pymysql

from PySide2 import QtCore
from PySide2.QtCore import *
from PySide2.QtWidgets import *
from PySide2.QtGui import *

from utils.canvas import Canvas
from utils.struct import *

QtCore.QCoreApplication.addLibraryPath(os.path.join(os.path.dirname(QtCore.__file__), "plugins"))
PATH_FILE = os.path.dirname(os.path.abspath(__file__))

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Set MainWindow setting
        self.setWindowTitle('HMI Prototype')
        self.resize(QSize(600, 500))

        # Set variables
        self.fileName = None
        self.jsonFile = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.openCamera)
        self.capture = cv2.VideoCapture(1)

        # Create canvas for showing and drawing image.
        self.img = QPixmap()
        self.canvas = Canvas(parent=self)

        # Create button.
        self.loadImage_btn = QPushButton('Load image')
        self.openCamera_btn = QPushButton('Open camera')
        self.loadRoi_btn = QPushButton('Load ROI')
        self.savePosition_btn = QPushButton('Save ROI')
        self.cleanROI_btn = QPushButton('Clean ROIs')
        self.captureImage_btn = QPushButton('Capture Image')
        self.detect_btn = QPushButton('Detect ROI')
        self.zoominImage_btn = QPushButton('Zoom in')
        self.zoomoutImage_btn = QPushButton('Zoom out')
        ## Connect slot of button.
        self.loadImage_btn.clicked.connect(self.loadImageSlot)
        self.openCamera_btn.clicked.connect(self.openCameraSlot)
        self.loadRoi_btn.clicked.connect(self.loadRoiSlot)
        self.savePosition_btn.clicked.connect(self.savePositionSlot)
        self.cleanROI_btn.clicked.connect(self.cleanRoiSlot)
        self.captureImage_btn.clicked.connect(self.captureImageSlot)
        self.detect_btn.clicked.connect(self.detectRoiSlot)
        self.zoominImage_btn.clicked.connect(self.zoomInImageSlot)
        self.zoomoutImage_btn.clicked.connect(self.zoomOutImageSlot)
        self.canvas.writeToDB.connect(self.insertDB)
        ## size policy of button.
        self.loadImage_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Ignored)
        self.openCamera_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Ignored)
        self.loadRoi_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Ignored)
        self.savePosition_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Ignored)
        self.cleanROI_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Ignored)
        self.captureImage_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Ignored)
        self.detect_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Ignored)
        self.zoominImage_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Ignored)
        self.zoomoutImage_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Ignored)

        # Create scroll area.
        scroll = QScrollArea()
        scroll.setWidget(self.canvas)
        scroll.setWidgetResizable(True)
        self.scrollArea = scroll
        self.scrollBars = {
            Qt.Vertical: scroll.verticalScrollBar(),
            Qt.Horizontal: scroll.horizontalScrollBar()
        }
        self.canvas.scrollRequest.connect(self.scrollRequest)

        # Set layout.
        layout = QHBoxLayout()
        ## Left layer.
        functionLayer = QVBoxLayout()
        functionLayer.setSpacing(10)                # Set each widget gap.
        functionLayer.setMargin(0)                  # Set margin of layer.
        functionLayer.addWidget(self.loadImage_btn)
        functionLayer.addWidget(self.loadRoi_btn)
        functionLayer.addWidget(self.savePosition_btn)
        functionLayer.addWidget(self.cleanROI_btn)
        functionLayer.addWidget(self.openCamera_btn)
        functionLayer.addWidget(self.captureImage_btn)
        functionLayer.addWidget(self.detect_btn)
        functionLayer.addWidget(self.zoominImage_btn)
        functionLayer.addWidget(self.zoomoutImage_btn)
        functionWidget = QWidget()
        functionWidget.setLayout(functionLayer)
        layout.addWidget(functionWidget)
        ## Right layer.
        layout.addWidget(self.scrollArea)
        layout.setStretchFactor(self.scrollArea, 20)
        ## Set stretching ratio of layout.
        layout.setStretchFactor(functionWidget, 1)      # Set stretching ratio 1:9
        layout.setStretchFactor(self.scrollArea, 9)

        # Create central widget of QMainWindow
        windowContainer = QWidget()
        windowContainer.setLayout(layout)
        self.setCentralWidget(windowContainer)

        # Set shortcuts.
        zoomIn = QShortcut(QKeySequence.ZoomIn, self, self.zoomInImageSlot)
        zoomOut = QShortcut(QKeySequence.ZoomOut, self, self.zoomOutImageSlot)
        drawing = QShortcut(QKeySequence('w'), self, self.onDrawing)
        delete = QShortcut(QKeySequence.Delete, self, self.canvas.deleteSelected)
        deleteKey = QShortcut(QKeySequence('d'), self, self.canvas.deleteSelected)
        saveROI = QShortcut(QKeySequence('s'), self, self.savePositionSlot)
        openCamera = QShortcut(QKeySequence('o'), self, self.openCameraSlot)
        pauseCamera = QShortcut(QKeySequence('p'), self, self.captureImageSlot)
        allActions = (zoomIn, zoomOut, drawing, delete, deleteKey, saveROI, openCamera, pauseCamera)
        for action in allActions:
            action.setEnabled(False)
        self.actions = struct(zoomIn=zoomIn, zoomOut=zoomOut, drawing=drawing, 
            delete=delete, deleteKey=deleteKey, saveROI=saveROI, 
            openCamera=open, pauseCamera=pauseCamera, allActions=allActions)

    def onDrawing(self):
        print('Drawing mode...')
        self.canvas.unhighlightShape()
        self.canvas.isDrawing = True

    # TODO: MainWindow resize event
    def resizeEvent(self, event):
        """QMainWindow event: MainWindow resize event."""
        # self.canvas.setMinimumSize(self.scrollArea.width(), self.scrollArea.height())

    def loadImageSlot(self):
        """Slot of loading image"""
        # Ask Y/N before loading image when shape is created.
        if self.canvas.shapes:
            if not self.discardChangesDialog():
                return
            self.canvas.shapes = []

        file, _ = QFileDialog.getOpenFileName(self, "Open Image", 
            PATH_FILE, "Image Files (*.png *.jpg *.bmp *.tiff)")
        print('file path: {}'.format(file))
        if file:
            self.fileName = os.path.splitext(os.path.basename(file))[0]
            self.img = QPixmap(file)
            if self.img:
                self.canvas.setGeometry(0, 0, self.canvas.width(), self.canvas.height())
                self.canvas.loadPixmap(self.img)

                for action in self.actions.allActions:
                    action.setEnabled(True)

    def savePositionSlot(self):
        """Slot of outputting the coordinate of each shape."""
        if self.fileName:
            self.canvas.savePosition(self.fileName)

    def cleanRoiSlot(self):
        """Clean all ROI."""
        self.canvas.shapes = []
        self.canvas.repaint()

    def openCameraSlot(self):
        """Slot of Setting timer to start to load frame from the camera."""
        self.timer.start(30)

    def loadRoiSlot(self):
        """Slot of showing ROI."""
        print('Show roi.')
        file, _ = QFileDialog.getOpenFileName(self, "Open ROI", PATH_FILE, "JSON Files (*.json)")
        print('file path: {}'.format(file))
        if file:
            self.jsonFile = file
            self.canvas.showPosition(self.jsonFile)

    def captureImageSlot(self):
        """Slot of Setting timer to stop to capture frame."""
        self.timer.stop()

    def detectRoiSlot(self):
        """Slot of detecting digits of ROI."""
        self.canvas.detectShape()

    def zoomInImageSlot(self):
        """Slot of zooming in image."""
        if self.img:
            value = self.canvas.scale
            value += 0.1
            self.canvas.zoom(value)
            self.canvas.adjustSize()
            canvas_position = self.canvas.geometry()
            print('Zoom in... Canvas size: {}'.format(canvas_position))

    def zoomOutImageSlot(self):
        """Slot of zooming out image."""
        if self.img:
            value = self.canvas.scale
            value -= 0.1
            self.canvas.zoom(value)
            self.canvas.adjustSize()
            canvas_position = self.canvas.geometry()
            print('Zoom out... Canvas size: {}'.format(canvas_position))

    def openCamera(self):
        """Open camera to get current frame."""
        ret, frame = self.capture.read()
        if ret == False:
            return
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # frame = cv2.flip(frame, 1)
        self.img = QPixmap(QImage(frame.data, frame.shape[1], frame.shape[0], 
            frame.strides[0], QImage.Format_RGB888))
        if self.img:
            self.canvas.setGeometry(0, 0, self.canvas.width(), self.canvas.height())
            self.canvas.loadPixmap(self.img)

    def insertDB(self, info):
        """Insert information to DB."""
        host = '127.0.0.1'
        user = 'root'
        pw = '12345678'
        db = 'sunstige_hmi_data'
        table = 'roi_info'

        conn = pymysql.connect(host, user, pw, db)
        cursor = conn.cursor()
        sql = "INSERT INTO `roi_info` \
            (`machineName`, `frameName`, `roiName`, `x`, `y`, `w`, `h`) \
            VALUES (%s, %s, %s, %s, %s, %s, %s)"

        try:
            cursor.execute(sql, info)
            conn.commit()
        except Exception as e:
            print(e)
        finally:
            conn.close()

    def discardChangesDialog(self):
        """Ask whether to discard all shapes."""
        yes, no = QMessageBox.Yes, QMessageBox.No
        msg = u'You have unsaved changes, proceed anyway?'
        return yes == QMessageBox.warning(self, 'Attention', msg, yes | no)

    def scrollRequest(self, delta, orientation):
        units = - delta / (8 * 15)
        bar = self.scrollBars[orientation]
        bar.setValue(bar.value() + bar.singleStep() * units)

def main():
    app = QApplication([])
    app.addLibraryPath(PATH_FILE)
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()