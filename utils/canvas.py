# Canvas for showing image and drawing ROIs
# TODO: uncomplete

from PySide2.QtGui import *
from PySide2.QtCore import *
from PySide2.QtWidgets import *

from utils.shape import Shape

# Cursor icon
CURSOR_DEFAULT = Qt.ArrowCursor
CURSOR_DRAW = Qt.CrossCursor 

class Canvas(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.pixmap = QPixmap()
        self._painter = QPainter()
        self.scale = 1.0
        self.shapes = []            # Create list to save object: Shape.
        self.currentShape = None    # Current selected shape.

        # Set widget options.
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.WheelFocus)

        # Set flag
        self._cursor = CURSOR_DEFAULT
        self.isDrawing = False

    def loadPixmap(self, pixmap):
        """Paint image on QWidget."""
        self.pixmap = pixmap

        # Calculate resize scale
        e = 2.0
        ori_width = self.width() - e
        ori_height = self.height() - e
        ori_aspect_ratio = ori_width / ori_height

        img_width = self.pixmap.width() - 0.0
        img_height = self.pixmap.height() - 0.0
        img_aspect_ratio = img_width / img_height

        self.scale = ori_width / img_width if img_aspect_ratio >= ori_aspect_ratio else ori_height / img_height

        self.repaint()

    def sizeHint(self):
        """QWidget event: Along with a call to adjustSize() are required for the scroll area"""
        return self.minimumSizeHint()

    def minimumSizeHint(self):
        """Along with a call to adjustSize() are required for the scroll area"""
        if self.pixmap:
            return self.scale * self.pixmap.size()
        return super(Canvas, self).minimumSizeHint()

    def paintEvent(self, event):
        """QWidget event: Paint event of painting image on QWidget"""
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

        # TODO: Draw rect
        for shape in self.shapes:
            if shape.endPos:
                shape.paintRect(p)

        # TODO: Drawing rect when mouse is moving.
        if self.isDrawing and self.currentShape:
            if self.currentShape.endPos:
                print('drawing rect...')
                leftTop = self.currentShape.firstPos
                rightBottom = self.currentShape.endPos
                rectWidth = rightBottom.x() - leftTop.x()
                rectHeight = rightBottom.y() - leftTop.y()
                p.setPen(QColor(255, 0, 0))
                brush = QBrush(Qt.BDiagPattern)
                p.setBrush(brush)
                p.drawRect(leftTop.x(), leftTop.y(), rectWidth, rectHeight)

        self.setAutoFillBackground(True)
        pal = self.palette()
        pal.setColor(self.backgroundRole(), QColor(226, 240, 217, 255))
        self.setPalette(pal)
        p.end()

    def outOfPixmap(self, p):
        w, h = self.pixmap.width(), self.pixmap.height()
        return not (0 <= p.x() <= w and 0 <= p.y() <= h)

    # TODO: When using wheel to zoom, need to calculate the zoom point
    def offsetToCenter(self):
        """Calculate the coordinate after translating"""
        s = self.scale
        area = super(Canvas, self).size()
        w, h = self.pixmap.width() * s, self.pixmap.height() * s
        aw, ah = area.width(), area.height()
        x = (aw - w) / (2 * s) if aw > w else 0
        y = (ah - h) / (2 * s) if ah > h else 0
        return QPointF(x, y)

    def zoom(self, value):
        """Zoom scale by value"""
        if (value >= 0.01) and (value <= 5.0):
            self.scale = value
            print('Current scale: {}'.format(self.scale))
            self.repaint()

    def transformPos(self, point):
        """Convert from widget-logical coordinates to painter-logical coordinates."""
        return point / self.scale - self.offsetToCenter().toPoint()

    # TODO: using wheel to zoom
    def wheelEvent(self, ev):
        """QWidget event: Scroll wheel event of zooming in or out"""
        delta = ev.angleDelta()
        h_delta = delta.x()
        v_delta = delta.y()
        mods = int(ev.modifiers())
        print('h_delta: {}'.format(h_delta))
        print('v_delta: {}'.format(v_delta))
        print('mods: {}'.format(mods))

        if Qt.ControlModifier == mods and v_delta:
            if v_delta > 0:
                print('zoom in')
                value = self.scale
                value += 0.1
                self.zoom(value)
                self.adjustSize()
            else:
                print('zoom out')
                value = self.scale
                value -= 0.1
                self.zoom(value)
                self.adjustSize()
        ev.accept()

    # TODO: mouse event
    def mouseMoveEvent(self, ev):
        """QWidget event: Mouse move evnet"""
        if self.isDrawing:
            self.overrideCursor(CURSOR_DRAW)
            if self.currentShape:
                pos = self.transformPos(ev.pos())
                if self.outOfPixmap(pos):
                    size = self.pixmap.size()
                    clippedX = min(max(1, pos.x()), size.width())
                    clippedY = min(max(1, pos.y()), size.height())
                    pos = QPoint(clippedX, clippedY)
                else:
                    # TODO: Attract line and point.
                    a = 0
                self.currentShape.endPos = pos
            self.repaint()

    def mousePressEvent(self, ev):
        """QWidget event: Mouse press evnet"""
        pos = self.transformPos(ev.pos())

        # Adjust position when coordinate is out of range(image.size).
        if self.outOfPixmap(pos):
            size = self.pixmap.size()
            clippedX = min(max(0, pos.x()), size.width())
            clippedY = min(max(0, pos.y()), size.height())
            pos = QPoint(clippedX, clippedY)
        print('Mouse press: {}'.format(pos))
        
        if ev.button() == Qt.LeftButton:
            if self.isDrawing:
                self.currentShape = Shape()     # Create Shape to save rect info.
                self.currentShape.firstPos = pos

    def mouseReleaseEvent(self, ev):
        """QWidget event: Mouse release evnet"""
        print('Release')
        if ev.button() == Qt.LeftButton:
            if self.isDrawing:
                # Reset flags.
                self.shapes.append(self.currentShape)   # Append to shape list.
                self.isDrawing = False
                self.currentShape = None
                self.restoreCursor()
                self.update()

    def enterEvent(self, ev):
        """QWidget event: When cursor enters QWidget."""
        self.overrideCursor(self._cursor)

    def leaveEvent(self, ev):
        """QWidget event: When cursor leaves QWidget."""
        # Restore to default cursor when leaves QWidget.
        self.restoreCursor()

    def overrideCursor(self, cursor):
        """QWidget event: Change cursor icon."""
        self._cursor = cursor
        if self.currentCursor() is None:
            QApplication.setOverrideCursor(cursor)
        else:
            QApplication.changeOverrideCursor(cursor)

    def currentCursor(self):
        """Determine whether the current cursor has been changed."""
        cursor = QApplication.overrideCursor()
        if cursor is not None:
            cursor = cursor.shape()
        return cursor

    def restoreCursor(self):
        """Restore cursor icon."""
        QApplication.restoreOverrideCursor()

if __name__ == "__main__":
    app = QApplication([])
    window = Canvas()
    window.show()
    app.exec_()
