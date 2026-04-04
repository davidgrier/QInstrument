from __future__ import annotations

import sys
import logging
from qtpy import QtWidgets, QtGui, QtCore
import numpy as np


logger = logging.getLogger(__name__)


class QJoystick(QtWidgets.QWidget):
    '''Mouse-controlled joystick widget.

    Renders a circular pad with a draggable knob. Press and drag the
    knob to set a position; release to return it to center.

    Signals
    -------
    positionChanged(numpy.ndarray)
        Emitted when the knob moves beyond the dead-band. Carries a
        two-element array ``[x, y]`` mapped linearly from the knob
        fraction ``[-1, 1]`` to ``[minimum, maximum]``.
        ``x`` is positive to the right; ``y`` is positive upward.

    Properties
    ==========
    fullscale : float
        Symmetric output limit: equivalent to ``setRange(-v, v)``.
        Default: 1.0.
    tolerance : float
        Fractional dead-band; position changes smaller than this
        fraction of the full pad radius are suppressed. Default: 0.05.
    '''

    positionChanged = QtCore.Signal(object)

    def __init__(self, *args,
                 fullscale: float | None = None,
                 **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.sizePolicy().setHeightForWidth(True)
        self.padding = 0.1
        self.knobSize = 0.3
        self.setRange(-(fullscale or 1.), fullscale or 1.)
        self.tolerance = 0.05
        self.position = QtCore.QPointF(0, 0)
        self._values = np.zeros(2)
        self.active = False

    def setRange(self, minimum: float, maximum: float) -> None:
        '''Set the output range for both axes.

        The knob fraction ``[-1, 1]`` maps linearly to
        ``[minimum, maximum]``, so the center position emits
        ``(minimum + maximum) / 2``.

        Parameters
        ----------
        minimum : float
            Output value at full negative deflection.
        maximum : float
            Output value at full positive deflection.
        '''
        self._minimum = minimum
        self._maximum = maximum

    def minimum(self) -> float:
        '''Return the output value at full negative deflection.'''
        return self._minimum

    def maximum(self) -> float:
        '''Return the output value at full positive deflection.'''
        return self._maximum

    @property
    def fullscale(self) -> float:
        '''Symmetric output limit; equivalent to ``setRange(-v, v)``.'''
        return self._maximum

    @fullscale.setter
    def fullscale(self, value: float) -> None:
        self.setRange(-value, value)

    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:
        '''Recompute the pad radius and knob travel limit on resize.'''
        self.radius = min(self.size().width(), self.size().height()) / 2
        self.radius *= (1. - self.padding)
        self.limit = (1. - self.knobSize) * self.radius

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        if self.isEnabled():
            pen = QtCore.Qt.GlobalColor.black
            bg = QtGui.QColor('#F8EEFF')
            knob = QtCore.Qt.GlobalColor.gray
        else:
            pen = QtCore.Qt.GlobalColor.darkGray
            bg = QtGui.QColor('#F8F8F8')
            knob = QtCore.Qt.GlobalColor.lightGray
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing, True)
        painter.setPen(pen)
        painter.setBrush(bg)
        painter.drawEllipse(self._limitRect())
        painter.setBrush(knob)
        painter.drawEllipse(self._knobRect())

    def _limitRect(self) -> QtCore.QRectF:
        '''Return the bounding rectangle of the outer pad circle.'''
        rect = np.array([-1, -1, 2, 2]) * self.radius
        return QtCore.QRectF(*rect).translated(self._center())

    def _knobRect(self) -> QtCore.QRectF:
        '''Return the bounding rectangle of the knob circle.

        When inactive the knob is drawn at the center; when active it
        follows :attr:`position`.
        '''
        size = self.radius * self.knobSize
        rect = np.array([-1, -1, 2, 2]) * size
        pos = self.position if self.active else self._center()
        return QtCore.QRectF(*rect).translated(pos)

    def _center(self) -> QtCore.QPointF:
        '''Return the widget center point.'''
        return QtCore.QPointF(self.width() / 2, self.height() / 2)

    def _limited(self, point: QtCore.QPointF) -> QtCore.QPointF:
        '''Clamp ``point`` to within the knob travel radius.

        Parameters
        ----------
        point : QtCore.QPointF
            Unclamped cursor position in widget coordinates.

        Returns
        -------
        QtCore.QPointF
            Nearest point on or inside the travel circle.
        '''
        limit_line = QtCore.QLineF(self._center(), point)
        if limit_line.length() > self.limit:
            limit_line.setLength(self.limit)
        return limit_line.p2()

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        '''Activate dragging when the press lands inside the knob.'''
        self.active = self._knobRect().contains(QtCore.QPointF(event.pos()))
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent) -> None:
        '''Deactivate dragging and return the knob to center.'''
        self.active = False
        self.position = QtCore.QPointF(0, 0)
        self.update()
        self._emitSignal()

    def mouseMoveEvent(self, event: QtGui.QMouseEvent) -> None:
        '''Update knob position while dragging.'''
        self.position = self._limited(QtCore.QPointF(event.pos()))
        self.update()
        self._emitSignal()

    def _fractions(self) -> np.ndarray:
        '''Return the current knob displacement as fractions of the travel radius.

        Returns
        -------
        numpy.ndarray
            Two-element array ``[fx, fy]`` in the range ``[-1, 1]``.
            ``fy`` is negated so that upward motion gives a positive value.
            Returns ``[0., 0.]`` when inactive.
        '''
        if self.active:
            displacement = QtCore.QLineF(self._center(), self.position)
            fx = min(displacement.dx() / self.limit, 1.)
            fy = -min(displacement.dy() / self.limit, 1.)
        else:
            fx, fy = 0., 0.
        return np.array([fx, fy])

    def _emitSignal(self) -> None:
        '''Emit :attr:`positionChanged` if the position changed beyond tolerance.

        Suppresses emission when the change from the last emitted value
        is within :attr:`tolerance` on both axes.
        '''
        values = self._fractions()
        if np.allclose(values, self._values, self.tolerance):
            return
        self._values = values
        lo, hi = self._minimum, self._maximum
        values = lo + (values + 1.) / 2. * (hi - lo)
        self.positionChanged.emit(values)
        logger.debug('{:.2f} {:.2f}'.format(*values))


def example() -> None:
    from qtpy.QtWidgets import QApplication

    def report(xy: np.ndarray) -> None:
        print('position: ({:+.2f}, {:+.2f})'.format(*xy), end='\r')

    app = QApplication.instance() or QApplication(sys.argv)
    joystick = QJoystick(fullscale=2.)
    joystick.positionChanged.connect(report)
    joystick.show()
    sys.exit(app.exec())


__all__ = ['QJoystick']


if __name__ == '__main__':
    example()
