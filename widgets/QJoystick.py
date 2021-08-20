from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import (QPainter, QPen, QBrush, QColor)
from PyQt5.QtCore import (Qt, QPointF, QLineF, QRectF,
                          pyqtSignal, pyqtProperty)
import numpy as np
import logging

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)


class QJoystick(QWidget):

    joystickChanged = pyqtSignal(object)
    
    def __init__(self, *args,
                 radius=None,
                 padding=None,
                 fullscale=None,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self.radius = radius or 40
        self.padding = padding or 5
        self.knobFraction = 0.3
        size = 2 * (self.radius + self.padding)
        self.setMinimumSize(size, size)
        self.joystickPosition = QPointF(0, 0)
        self.limit = (1. - self.knobFraction) * self.radius
        self.fullscale = fullscale or 1.
        self.tolerance = 0.1 * self.fullscale
        self._values = np.zeros(2)
        self.active = False

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setPen(QPen(Qt.black, 2, Qt.SolidLine))
        painter.setBrush(QColor('#F8EEFF'))
        painter.drawEllipse(self._ring())
        painter.setBrush(QBrush(Qt.gray, Qt.SolidPattern))
        painter.drawEllipse(self._knob())

    def _ring(self):
        rect = np.array([-1, -1, 2, 2]) * self.radius
        return QRectF(*rect).translated(self._center())
    
    def _knob(self):
        size = self.radius * self.knobFraction
        rect = np.array([-1, -1, 2, 2]) * size
        pos = self.knobPosition if self.active else self._center()
        return QRectF(*rect).translated(pos)

    def _center(self):
        return QPointF(self.width()/2, self.height()/2)

    def _boundJoystick(self, point):
        limitLine = QLineF(self._center(), point)
        if (limitLine.length() > self.limit):
            limitLine.setLength(self.limit)
        return limitLine.p2()

    def fractions(self):
        if self.active:
            displacement = QLineF(self._center(), self.knobPosition)
            fx = min(displacement.dx() / self.limit, 1.)
            fy = -min(displacement.dy() / self.limit, 1.)
        else:
            fx, fy = 0., 0.
        return np.array([fx, fy])

    def mousePressEvent(self, ev):
        self.active = self._knob().contains(ev.pos())
        return super().mousePressEvent(ev)

    def mouseReleaseEvent(self, event):
        self.active = False
        self.knobPosition = QPointF(0, 0)
        self.update()
        self.emitSignal()

    def mouseMoveEvent(self, event):
        self.knobPosition = self._boundJoystick(event.pos())
        self.update()
        self.emitSignal()

    def emitSignal(self):
        values = self.fullscale * self.fractions()
        if np.allclose(values, self._values, self.tolerance):
            return
        self._values = values
        self.joystickChanged.emit(values)
        logger.debug('{:.2f} {:.2f}'.format(*values))


if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    joystick = QJoystick()
    joystick.show()
    sys.exit(app.exec_())

    ## Start Qt event loop unless running in interactive mode or using pyside.
    #if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
    #    QApplication.instance().exec_()
