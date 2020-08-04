from PySide2.QtGui import *
from PySide2.QtCore import *
from PySide2.QtWidgets import *

class Shape(object):
    def __init__(self):
        self.firstPos = None
        self.endPos = None
        self.digit = None

    def size(self):
        width = self.endPos.x() - self.firstPos.x()
        height = self.endPos.y() - self.firstPos.y()
        return (width, height)

    def paintRect(self, painter):
        # Draw rectangle.
        leftTop = self.firstPos
        rightBottom = self.endPos
        rectWidth = rightBottom.x() - leftTop.x()
        rectHeight = rightBottom.y() - leftTop.y()
        painter.setPen(QColor(0, 255, 0))
        painter.drawRect(leftTop.x(), leftTop.y(), rectWidth, rectHeight)

        # Draw text at the top-left
        if self.digit is not None:
            textX = self.firstPos.x()
            textY = self.firstPos.y() - 2
            if textY < 10:      # If position is too top.
                textY += 10
            font = QFont()
            font.setPointSize(8)
            painter.setFont(font)
            painter.drawText(textX, textY, str(self.digit))
            
    def isInShape(self, point):
        if (self.firstPos.x() <= point.x() <= self.endPos.x()) \
            and (self.firstPos.y() <= point.y() <= self.endPos.y()):
            return True
        else:
            return False