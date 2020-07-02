# Canvas for showing image and drawing ROIs
# TODO: uncomplete

from PySide2.QtGui import *
from PySide2.QtCore import *
from PySide2.QtWidgets import *

class Canvas(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # self.setGeometry(300, 300, 800, 400)
        
        # Set line width on QLabel
        # # self.resize(500, 500)
        # self.setFrameShape(QFrame.Box)
        # self.setLineWidth(5)
        # self.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        # self.setBackgroundRole(QPalette.Dark)
        # # self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        # self.setScaledContents(True)

        # Initial QWidget
        self.pixmap = QPixmap()
        self._painter = QPainter()
        self.scale = 1.0

    # TODO: Paint image on QWidget
    def loadPixmap(self, pixmap):
        self.pixmap = pixmap

        # TODO: Calculate resize scale
        e = 2.0
        ori_width = self.width() - e
        ori_height = self.height() - e
        ori_aspect_ratio = ori_width / ori_height

        img_width = self.pixmap.width() - 0.0
        img_height = self.pixmap.height() - 0.0
        img_aspect_ratio = img_width / img_height

        self.scale = ori_width / img_width if img_aspect_ratio >= ori_aspect_ratio else ori_height / img_height

        self.repaint()

    # TODO: QWidget paint event
    def paintEvent(self, event):
        if not self.pixmap:
            return super(Canvas, self).paintEvent(event)

        p = self._painter
        p.begin(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.HighQualityAntialiasing)
        p.setRenderHint(QPainter.SmoothPixmapTransform)

        p.scale(self.scale, self.scale)
        p.translate(self.offsetToCenter())

        p.drawPixmap(0, 0, self.pixmap)

        self.setAutoFillBackground(True)
        pal = self.palette()
        pal.setColor(self.backgroundRole(), QColor(226, 240, 217, 255))
        self.setPalette(pal)
        p.end()

    def offsetToCenter(self):
        s = self.scale
        area = super(Canvas, self).size()
        w, h = self.pixmap.width() * s, self.pixmap.height() * s
        aw, ah = area.width(), area.height()
        x = (aw - w) / (2 * s) if aw > w else 0
        y = (ah - h) / (2 * s) if ah > h else 0
        return QPointF(x, y)


    # # TODO: zoomin zoomout event
    def zoom(self, value):
        self.scale = value
        print(self.scale)
        self.repaint()

    # def wheelEvent(self, ev):
    #     delta = ev.angleDelta()
    #     h_delta = delta.x()
    #     v_delta = delta.y()
    #     mods = int(ev.modifiers())
    #     print('h_delta: {}'.format(h_delta))
    #     print('v_delta: {}'.format(v_delta))
    #     print('mods: {}'.format(mods))

    #     if Qt.ControlModifier == mods and v_delta:
    #         self.zoomRequest.emit(v_delta)
    #         print('zoomRequest')
    #     else:
    #         v_delta and self.scrollRequest.emit(v_delta, Qt.Vertical)
    #         h_delta and self.scrollRequest.emit(h_delta, Qt.Horizontal)
    #     ev.accept()

if __name__ == "__main__":
    app = QApplication([])
    window = Canvas()
    window.show()
    app.exec_()
