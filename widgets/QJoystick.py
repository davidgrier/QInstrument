from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import (QPainter, QPen, QBrush, QColor)
from PyQt5.QtCore import (Qt, QPointF, QLineF, QRectF,
                          pyqtSignal, pyqtProperty)
import numpy as np
import logging

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class QJoystick(QWidget):

    positionChanged = pyqtSignal(object)

    def __init__(self, *args,
                 fullscale=None,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self.sizePolicy().setHeightForWidth(True)
        self.padding = 0.2
        self.knobSize = 0.3
        self.fullscale = fullscale or 1.
        self.tolerance = 0.05
        self.position = QPointF(0, 0)
        self._values = np.zeros(2)
        self.active = False

    def resizeEvent(self, event):
        self.radius = min(self.size().width(), self.size().height()) / 2
        self.radius *= (1. - self.padding)
        self.limit = (1. - self.knobSize) * self.radius
        
    def paintEvent(self, event):
        if self.isEnabled():
            pen, bg, knob = Qt.black, QColor('#F8EEFF'), Qt.gray
        else:
            pen, bg, knob = Qt.darkGray, QColor('#F8F8F8'), Qt.lightGray
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(pen)
        painter.setBrush(bg)
        painter.drawEllipse(self._limitRect())
        painter.setBrush(knob)
        painter.drawEllipse(self._knobRect())

    def _limitRect(self):
        rect = np.array([-1, -1, 2, 2]) * self.radius
        return QRectF(*rect).translated(self._center())

    def _knobRect(self):
        size = self.radius * self.knobSize
        rect = np.array([-1, -1, 2, 2]) * size
        pos = self.position if self.active else self._center()
        return QRectF(*rect).translated(pos)

    def _center(self):
        return QPointF(self.width()/2, self.height()/2)

    def _limited(self, point):
        limitLine = QLineF(self._center(), point)
        if (limitLine.length() > self.limit):
            limitLine.setLength(self.limit)
        return limitLine.p2()

    def mousePressEvent(self, ev):
        self.active = self._knobRect().contains(ev.pos())
        return super().mousePressEvent(ev)

    def mouseReleaseEvent(self, event):
        self.active = False
        self.position = QPointF(0, 0)
        self.update()
        self.emitSignal()

    def mouseMoveEvent(self, event):
        self.position = self._limited(event.pos())
        self.update()
        self.emitSignal()

    def _fractions(self):
        if self.active:
            displacement = QLineF(self._center(), self.position)
            fx = min(displacement.dx() / self.limit, 1.)
            fy = -min(displacement.dy() / self.limit, 1.)
        else:
            fx, fy = 0., 0.
        return np.array([fx, fy])
    
    def emitSignal(self):
        values = self._fractions()
        if np.allclose(values, self._values, self.tolerance):
            return
        self._values = values
        values *= self.fullscale
        self.positionChanged.emit(values)
        logger.debug('{:.2f} {:.2f}'.format(*values))


if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    joystick = QJoystick()
    joystick.show()
    sys.exit(app.exec_())
