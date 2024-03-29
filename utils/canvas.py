# Canvas for showing image and drawing ROIs.
# Uncomplete

import json
import time
import numpy as np

from PySide2.QtGui import *
from PySide2.QtCore import *
from PySide2.QtWidgets import *

from utils.shape import Shape
from utils.aimodel import AiModel
from utils.roiDialog import ROIDialog

# Cursor icon
CURSOR_DEFAULT = Qt.ArrowCursor
CURSOR_DRAW = Qt.CrossCursor 
CURSOR_GRAB = Qt.OpenHandCursor
CURSOR_MOVE = Qt.ClosedHandCursor

class Canvas(QWidget):
    writeToDB = Signal(list)
    zoomRequest = Signal(int)
    scrollRequest = Signal(int, int)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.pixmap = QPixmap()
        self._painter = QPainter()
        self.scale = 1.0
        self.shapes = []            # Create list to save object: Shape.
        self.currentShape = None    # Current selected shape.
        self.selectedShape = None   # Select shape if mouse left button click.
        self.prevPoint = QPointF()  # Save first point when mouse click on the shape.
        self.roiDialog = None       # Dialog of entering description of ROI.

        # Set widget options.
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.WheelFocus)

        # Set flag
        self._cursor = CURSOR_DEFAULT
        self.isDrawing = False

        # Ai model
        self.ROIDetector = AiModel(
            'model/yolov4-hmi_roi_2.cfg',
            'model/yolov4-hmi_roi_2_8000_1027.weights',
            'model/hmi_roi.data'
        )

        # self.ROIDetector = AiModel(
        #     'model/yolov4_test01.cfg',
        #     'model/yolov4_test01_best.weights',
        #     'model/test01.data'
        # )

        self.digitDetector = AiModel(
            'model/yolov4-digits.cfg',
            'model/yolov4-digits_best.weights',
            'model/digit.data'
        )

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
        h_delta = delta.x()
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
        else:
            v_delta and self.scrollRequest.emit(v_delta, Qt.Vertical)
            h_delta and self.scrollRequest.emit(h_delta, Qt.Horizontal)
        ev.accept()

        self.position = (800, 600)

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
                # Dialog of entering description of ROI.
                self.roiDialog = ROIDialog(parent=self)
                machineName, frameName, roiName = self.roiDialog.popUp(text='')

                if None not in [machineName, frameName, roiName]:
                    # Adjust rect point if self.firstPos isn's leftTop etc.
                    minX = min(self.currentShape.firstPos.x(), self.currentShape.endPos.x())
                    maxX = max(self.currentShape.firstPos.x(), self.currentShape.endPos.x())
                    minY = min(self.currentShape.firstPos.y(), self.currentShape.endPos.y())
                    maxY = max(self.currentShape.firstPos.y(), self.currentShape.endPos.y())

                    # Cannel shape when distance is too small.
                    if self.isTooSmall(minX, maxX, minY, maxY):
                        self.resetFlags()
                        return

                    # Record ROI informatino.
                    self.currentShape.firstPos = QPointF(minX, minY)
                    self.currentShape.endPos = QPointF(maxX, maxY)
                    self.currentShape.machineName = machineName
                    self.currentShape.frameName = frameName
                    self.currentShape.roiName = roiName
                    # Append to shape list.
                    self.shapes.append(self.currentShape)
                    self.restoreCursor()
                    self.resetFlags()
                else:
                    # Cancel drawn ROI.
                    self.currentShape = None
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
        shape.isSelected = True
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
        self.roiDialog = None
        self.update()

    def deleteSelected(self):
        """Delete the selected shape."""
        if self.selectedShape:
            self.shapes.remove(self.selectedShape)
            self.selectedShape.isSelected = False
            self.selectedShape = None
            self.update()

    def deselectShape(self):
        """Deselect the shape."""
        if self.selectedShape:
            self.selectedShape.isSelected = False
            self.selectedShape = None
            self.update()

    def showPosition(self, fileName):
        """Show coordinate of each shape on the canvas."""
        self.shapes = []
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
        """Output coordinate (x, y , w, h) of each shape."""
        if not self.shapes:
            return

        # Show saving dialog to set storage path.
        savedName, _ = QFileDialog.getSaveFileName(self, 'Save ROIs', fileName + '.json', 'JSON Files (*.json)')
        if savedName:
            data = {}
            # Get all information from shape.
            for i, shape in enumerate(self.shapes):
                x, y = shape.firstPos.x(), shape.firstPos.y()
                w = shape.endPos.x() - shape.firstPos.x()
                h = shape.endPos.y() - shape.firstPos.y()
                mainKey = 'ROI_{}'.format(i)
                machineName = shape.machineName
                frameName = shape.frameName
                roiName = shape.roiName
                position = [x, y, w, h]
                data[mainKey] = {
                    'machineName': machineName,
                    'frameName': frameName,
                    'roiName': roiName,
                    'position': position
                }

                # Write to DB.
                info = [machineName, frameName, roiName, x, y, w, h]
                self.writeToDB.emit(info)

            # Save file.
            with open(savedName, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            print('Saving ROI: {}'.format(savedName))

    def detectShape(self):
        """Detect all digits in the shapes."""
        if (self.pixmap is not None) :#and (self.shapes):
            # Convert QImage to np array.
            print('Start detecting: {}'.format(time.perf_counter()))
            img = self.pixmap.toImage()
            ptr = img.bits().tobytes()
            npImage = np.frombuffer(ptr, dtype=np.uint8).reshape(
                (self.pixmap.height(), self.pixmap.width(), 4))

            # Implement two-stage detection.
            # Detect ROIs.
            detections = self.ROIDetector.detectROI([npImage[:, :, 0:3]], isDebug=False)
            for i, detection in enumerate(detections):
                coordinate = detection[2]
                xmin, ymin, xmax, ymax = self.convertCoordinate(
                    list(coordinate), 
                    self.ROIDetector.model_size,
                    (npImage.shape[1], npImage.shape[0])
                )

                temp_shape = Shape()
                # Record ROI information.
                temp_shape.firstPos = QPointF(xmin, ymin)
                temp_shape.endPos = QPointF(xmax, ymax)
                temp_shape.machineName = str(i)
                temp_shape.frameName = str(i)
                temp_shape.roiName = str(i)
                # Append to shape list.
                self.shapes.append(temp_shape)

            # Detect digit by all ROIs.
            for i, shape in enumerate(self.shapes):
                # Get (x, y, w, h) from ROI.
                x, y = int(shape.firstPos.x()), int(shape.firstPos.y())
                w = int(shape.endPos.x() - shape.firstPos.x())
                h = int(shape.endPos.y() - shape.firstPos.y())

                # Crop image and select RGB channel without Alpha
                cropImage = npImage[y:y + h, x:x + w, 0:3]
                
                # Detect digits.
                shape.digit = self.digitDetector.detectDigit(cropImage, isDebug=False)
            print('End detecting: {}'.format(time.perf_counter()))
            self.repaint()

    def convertCoordinate(self, detection, ori_size, resize_size):
        """Convert coordinate from ori_size to resize_size then return xmin, ymin, xmax, ymax."""
        ow, oh = ori_size[0], ori_size[1]
        rw, rh = resize_size[0], resize_size[1]
        x, y, w, h = detection[0], detection[1], detection[2], detection[3]

        x = x * rw / ow
        y = y * rh / oh
        w = w * rw / ow
        h = h * rh / oh
        
        xmin = int(round(x - (w / 2)))
        xmax = int(round(x + (w / 2)))
        ymin = int(round(y - (h / 2)))
        ymax = int(round(y + (h / 2)))
        return xmin, ymin, xmax, ymax

    def unhighlightShape(self):
        """Unhighlight shape."""
        if self.selectedShape:
            self.selectedShape.isSelected = False

    def isTooSmall(self, x1, x2, y1, y2):
        """Determine whether the area of shape is too small."""
        if (x2 - x1 <= 3) or (y2 - y1 <= 3):
            return True
        return False

if __name__ == "__main__":
    app = QApplication([])
    window = Canvas()
    window.show()
    app.exec_()
