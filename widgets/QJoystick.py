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
        self._setupUi(fullscale)

    def _setupUi(self, fullscale: float | None) -> None:
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
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing, True)
        enabled = self.isEnabled()
        self._drawPad(painter, enabled)
        self._drawCrosshair(painter, enabled)
        self._drawRimHighlight(painter, enabled)
        self._drawKnobShadow(painter)
        self._drawKnob(painter, enabled)

    def _drawPad(self, painter: QtGui.QPainter, enabled: bool) -> None:
        '''Fill the pad with a radial gradient and draw its border.'''
        rect = self._limitRect()
        c = rect.center()
        r = rect.width() / 2.
        grad = QtGui.QRadialGradient(c.x(), c.y(), r)
        if enabled:
            grad.setColorAt(0., QtGui.QColor('#ede5f8'))
            grad.setColorAt(1., QtGui.QColor('#9878b8'))
        else:
            grad.setColorAt(0., QtGui.QColor('#f4f4f4'))
            grad.setColorAt(1., QtGui.QColor('#c0c0c0'))
        border = QtGui.QColor('#7060a0' if enabled else '#909090')
        painter.setPen(QtGui.QPen(border, 1.5))
        painter.setBrush(QtGui.QBrush(grad))
        painter.drawEllipse(rect)

    def _drawCrosshair(self, painter: QtGui.QPainter, enabled: bool) -> None:
        '''Draw faint axis lines through the pad center.'''
        c = self._center()
        r = self.radius
        color = QtGui.QColor('#503c64' if enabled else '#a0a0a0')
        color.setAlpha(80)
        pen = QtGui.QPen(color, 1.0, QtCore.Qt.PenStyle.DashLine)
        painter.setPen(pen)
        painter.drawLine(QtCore.QPointF(c.x() - r, c.y()),
                         QtCore.QPointF(c.x() + r, c.y()))
        painter.drawLine(QtCore.QPointF(c.x(), c.y() - r),
                         QtCore.QPointF(c.x(), c.y() + r))

    def _drawRimHighlight(self, painter: QtGui.QPainter, enabled: bool) -> None:
        '''Draw a bright arc across the upper-left rim to suggest a bevel.'''
        rect = self._limitRect()
        color = QtGui.QColor('#d8c8f0' if enabled else '#d8d8d8')
        painter.setPen(QtGui.QPen(color, 2.0))
        painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)
        painter.drawArc(rect, 45 * 16, 135 * 16)

    def _drawKnobShadow(self, painter: QtGui.QPainter) -> None:
        '''Draw a soft drop shadow behind the knob.'''
        rect = self._knobRect()
        offset = rect.width() * 0.12
        shadow = rect.translated(offset, offset)
        shadow.adjust(-offset * 0.2, -offset * 0.2,
                       offset * 0.2,  offset * 0.2)
        painter.setPen(QtCore.Qt.PenStyle.NoPen)
        painter.setBrush(QtGui.QColor(0, 0, 0, 55))
        painter.drawEllipse(shadow)

    def _drawKnob(self, painter: QtGui.QPainter, enabled: bool) -> None:
        '''Draw the knob as a sphere with a radial gradient and specular dot.'''
        rect = self._knobRect()
        c = rect.center()
        r = rect.width() / 2.
        # Focal point offset toward top-left for the lighting illusion
        fx, fy = c.x() - 0.3 * r, c.y() - 0.3 * r
        grad = QtGui.QRadialGradient(c.x(), c.y(), r, fx, fy)
        if enabled:
            grad.setColorAt(0., QtGui.QColor('#dce4ff'))
            grad.setColorAt(1., QtGui.QColor('#2838a8'))
        else:
            grad.setColorAt(0., QtGui.QColor('#e0e0e8'))
            grad.setColorAt(1., QtGui.QColor('#707080'))
        painter.setPen(QtCore.Qt.PenStyle.NoPen)
        painter.setBrush(QtGui.QBrush(grad))
        painter.drawEllipse(rect)
        # Specular highlight
        sr = r * 0.22
        spec = QtCore.QRectF(fx - 0.7 * sr - sr, fy - 0.5 * sr - sr,
                              sr * 2, sr * 2)
        painter.setBrush(QtGui.QColor(255, 255, 255, 190))
        painter.drawEllipse(spec)

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
