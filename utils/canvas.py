# Canvas for showing image and drawing ROIs.
# Uncomplete

import json
from PySide2.QtGui import *
from PySide2.QtCore import *
from PySide2.QtWidgets import *

from utils.shape import Shape

# Cursor icon
CURSOR_DEFAULT = Qt.ArrowCursor
CURSOR_DRAW = Qt.CrossCursor 
CURSOR_GRAB = Qt.OpenHandCursor
CURSOR_MOVE = Qt.ClosedHandCursor

class Canvas(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.pixmap = QPixmap()
        self._painter = QPainter()
        self.scale = 1.0
        self.shapes = []            # Create list to save object: Shape.
        self.currentShape = None    # Current selected shape.
        self.selectedShape = None   # Select shape if mouse left button click.
        self.prevPoint = QPointF()  # Save first point when mouse click on the shape.

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
        self.scale = max( min(self.scale, 5.0), 0.01 )      # Reset scale if scale if out of range.
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

        # Draw rect
        for shape in self.shapes:
            if shape.endPos:
                shape.paintRect(p)

        # Drawing rect when mouse is moving.
        if self.isDrawing and self.currentShape:
            if self.currentShape.endPos:
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
        else:
            print('Scale ({}) is out of range.'.format(self.scale))

    def transformPos(self, point):
        """Convert from widget-logical coordinates to painter-logical coordinates."""
        return point / self.scale - self.offsetToCenter().toPoint()

    def wheelEvent(self, ev):
        """QWidget event: Scroll wheel event of zooming in or out"""
        delta = ev.angleDelta()
        v_delta = delta.y()
        mods = int(ev.modifiers())

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

    def mouseMoveEvent(self, ev):
        """QWidget event: Mouse move evnet"""
        pos = self.transformPos(ev.pos())

        if self.isDrawing:
            self.overrideCursor(CURSOR_DRAW)
            if self.currentShape:
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
            return

        if Qt.LeftButton & ev.buttons():
            # Move rectangle.
            if self.selectedShape:
                if self.selectedShape.isInShape(pos):
                    self.overrideCursor(CURSOR_MOVE)
                    self.moveShape(self.selectedShape, pos)
                    return

        # Change cursor icon when moving on ROI.
        for shape in reversed([s for s in self.shapes]):
            if shape.isInShape(pos):
                self.overrideCursor(CURSOR_GRAB)
                self.update()
                break
        else:
            self.overrideCursor(CURSOR_DEFAULT)

    def mousePressEvent(self, ev):
        """QWidget event: Mouse press evnet"""
        pos = self.transformPos(ev.pos())

        # Adjust position when coordinate is out of range(image.size).
        if self.outOfPixmap(pos):
            size = self.pixmap.size()
            clippedX = min(max(0, pos.x()), size.width())
            clippedY = min(max(0, pos.y()), size.height())
            pos = QPoint(clippedX, clippedY)
        
        if ev.button() == Qt.LeftButton:
            if self.isDrawing:
                self.selectedShape = None
                self.currentShape = Shape()     # Create Shape to save rect info.
                self.currentShape.firstPos = pos
            else:
                # Select shape
                self.selectShapePoint(pos)
                self.prevPoint = pos        # Save point when wanna move.
                self.repaint()

    def mouseReleaseEvent(self, ev):
        """QWidget event: Mouse release evnet"""
        if ev.button() == Qt.LeftButton and self.selectedShape:
            self.overrideCursor(CURSOR_GRAB)
            self.resetFlags()

        elif ev.button() == Qt.LeftButton:
            if self.isDrawing:
                # Adjust rect point if self.firstPos isn's leftTop etc.
                minX = min(self.currentShape.firstPos.x(), self.currentShape.endPos.x())
                maxX = max(self.currentShape.firstPos.x(), self.currentShape.endPos.x())
                minY = min(self.currentShape.firstPos.y(), self.currentShape.endPos.y())
                maxY = max(self.currentShape.firstPos.y(), self.currentShape.endPos.y())
                self.currentShape.firstPos = QPointF(minX, minY)
                self.currentShape.endPos = QPointF(maxX, maxY)
                self.shapes.append(self.currentShape)   # Append to shape list.
                self.restoreCursor()
                self.resetFlags()

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

    def selectShapePoint(self, point):
        """Select the first shape created which contains this point."""
        self.deselectShape()
        for shape in reversed(self.shapes):
            if shape.isInShape(point):
                self.selectShape(shape)
                return

    def selectShape(self, shape):
        """Select and assign shape."""
        self.selectedShape = shape
        self.update()

    def moveShape(self, shape, point):
        """Move rectangle."""
        width = shape.size()[0]
        height = shape.size()[1]
        maxWidth = self.pixmap.width()
        maxHeight = self.pixmap.height()

        # Calculate firstPos and endPos of shape.
        adjustedFirstPosX = point.x() - width / 2
        adjustedFirstPosY = point.y() - height / 2
        adjustedEndPosX = point.x() + width / 2
        adjustedEndPosY = point.y() + height / 2

        # Confirm if the coordinate is within the range.
        adjustedFirstPosX = max( min(adjustedFirstPosX, maxWidth - width), 0 )
        adjustedFirstPosY = max( min(adjustedFirstPosY, maxHeight - height), 0 )
        adjustedEndPosX = max( min(adjustedEndPosX, maxWidth), width )
        adjustedEndPosY = max( min(adjustedEndPosY, maxHeight), height )

        # Modify position.
        shape.firstPos = QPoint(adjustedFirstPosX, adjustedFirstPosY)
        shape.endPos = QPoint(adjustedEndPosX, adjustedEndPosY)
        self.repaint()
    
    def resetFlags(self):
        """Reset flags."""
        self.isDrawing = False
        self.currentShape = None
        # self.selectedShape = None
        self.update()

    def deleteSelected(self):
        """Delete the selected shape."""
        if self.selectedShape:
            self.shapes.remove(self.selectedShape)
            self.selectedShape = None
            self.update()

    def deselectShape(self):
        """Deselect the shape."""
        if self.selectedShape:
            self.selectedShape = None
            self.update()

    def showPosition(self, fileName):
        # TODO: show roi coordinate
        """Show coordinate of each shape on the canvas."""
        with open(fileName, 'r', encoding='UTF-8') as f:
            roiJson = json.load(f)
            for i, key in enumerate(roiJson):
                w, h = roiJson[key]['position'][2], roiJson[key]['position'][3]
                firstPos = QPoint(roiJson[key]['position'][0], 
                    roiJson[key]['position'][1])
                endPos = QPoint(firstPos.x() + w, firstPos.y() + h)

                tempShape = Shape()
                tempShape.firstPos = firstPos
                tempShape.endPos = endPos
                self.shapes.append(tempShape)

                self.repaint()

    def savePosition(self, fileName):
        """Output coordinate of each shape."""
        if not self.shapes:
            return
        data = {}
        # Get all information from shape.
        for i, shape in enumerate(self.shapes):
            x, y = shape.firstPos.x(), shape.firstPos.y()
            w = shape.endPos.x() - shape.firstPos.x()
            h = shape.endPos.y() - shape.firstPos.y()
            mainKey = 'ROI_{}'.format(i)
            descripiton = ''
            position = [x, y, w, h]
            data[mainKey] = {
                'description': descripiton,
                'position': position
            }

        # Save file.
        filePath = 'output/{}_ROI.json'.format(fileName)
        with open(filePath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print('Saving ROI: {}'.format(filePath))

if __name__ == "__main__":
    app = QApplication([])
    window = Canvas()
    window.show()
    app.exec_()
