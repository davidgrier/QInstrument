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
    padColor : QtGui.QColor
        Base color of the pad. Gradient stops and border are derived
        from it via ``lighter()`` / ``darker()``.
        Default: ``QColor('#a888c8')`` (medium lavender).
        Settable via stylesheet: ``qproperty-padColor: #rrggbb;``
    knobColor : QtGui.QColor
        Base color of the knob. Gradient stops are derived from it.
        Default: ``QColor('#3848b8')`` (medium blue).
        Settable via stylesheet: ``qproperty-knobColor: #rrggbb;``
    tolerance : float
        Fractional dead-band; position changes smaller than this
        fraction of the full pad radius are suppressed. Default: 0.05.
    '''

    positionChanged = QtCore.Signal(object)

    _DISABLED_PAD_LIGHT  = QtGui.QColor(244, 244, 244)
    _DISABLED_PAD_DARK   = QtGui.QColor(192, 192, 192)
    _DISABLED_PAD_BORDER = QtGui.QColor(144, 144, 144)
    _DISABLED_CROSS      = QtGui.QColor(160, 160, 160, 80)
    _DISABLED_RIM        = QtGui.QColor(216, 216, 216, 180)
    _DISABLED_KNOB_LIGHT = QtGui.QColor(224, 224, 232)
    _DISABLED_KNOB_DARK  = QtGui.QColor(112, 112, 128)

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
        self._padColor = QtGui.QColor('#a888c8')
        self._knobColor = QtGui.QColor('#3848b8')
        self.position = QtCore.QPointF(0, 0)
        self._values = np.zeros(2)
        self.active = False
        self.radius = 0.
        self.limit = 0.

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

    def _getPadColor(self) -> QtGui.QColor:
        return self._padColor

    def _setPadColor(self, color: QtGui.QColor) -> None:
        self._padColor = color
        self.update()

    padColor = QtCore.Property('QColor', _getPadColor, _setPadColor)

    def setPadColor(self, color: QtGui.QColor) -> None:
        '''Set the base pad color and repaint.

        Gradient stops and border are derived automatically via
        ``lighter()`` / ``darker()``.  May also be set via stylesheet
        with ``qproperty-padColor: #rrggbb;``.

        Parameters
        ----------
        color : QtGui.QColor
            Base color for the pad.
        '''
        self._setPadColor(color)

    def _getKnobColor(self) -> QtGui.QColor:
        return self._knobColor

    def _setKnobColor(self, color: QtGui.QColor) -> None:
        self._knobColor = color
        self.update()

    knobColor = QtCore.Property('QColor', _getKnobColor, _setKnobColor)

    def setKnobColor(self, color: QtGui.QColor) -> None:
        '''Set the base knob color and repaint.

        Gradient stops are derived automatically via
        ``lighter()`` / ``darker()``.  May also be set via stylesheet
        with ``qproperty-knobColor: #rrggbb;``.

        Parameters
        ----------
        color : QtGui.QColor
            Base color for the knob.
        '''
        self._setKnobColor(color)

    def sizeHint(self) -> QtCore.QSize:
        '''Return the preferred widget size.'''
        return QtCore.QSize(120, 120)

    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:
        '''Recompute the pad radius and knob travel limit on resize.'''
        self.radius = min(self.size().width(), self.size().height()) / 2
        self.radius *= (1. - self.padding)
        self.limit = (1. - self.knobSize) * self.radius

    def setKnobFraction(self, fx: float, fy: float) -> None:
        '''Position the knob at a given fraction of the travel range.

        Intended for external control (e.g. step buttons on a
        :class:`QJoystickPad`).  Does not emit :attr:`positionChanged`.

        Parameters
        ----------
        fx : float
            Horizontal fraction in ``[-1, 1]``.  Positive is right.
        fy : float
            Vertical fraction in ``[-1, 1]``.  Positive is upward.
        '''
        if fx == 0. and fy == 0.:
            self.active = False
            self.position = QtCore.QPointF(0., 0.)
        else:
            c = self._center()
            self.position = QtCore.QPointF(c.x() + fx * self.limit,
                                           c.y() - fy * self.limit)
            self.active = True
        self.update()

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
            grad.setColorAt(0., self._padColor.lighter(155))
            grad.setColorAt(1., self._padColor.darker(108))
            border = self._padColor.darker(130)
        else:
            grad.setColorAt(0., self._DISABLED_PAD_LIGHT)
            grad.setColorAt(1., self._DISABLED_PAD_DARK)
            border = self._DISABLED_PAD_BORDER
        painter.setPen(QtGui.QPen(border, 1.5))
        painter.setBrush(QtGui.QBrush(grad))
        painter.drawEllipse(rect)

    def _drawCrosshair(self, painter: QtGui.QPainter, enabled: bool) -> None:
        '''Draw faint axis lines through the pad center.'''
        c = self._center()
        r = self.radius
        if enabled:
            color = self._padColor.darker(160)
            color.setAlpha(80)
        else:
            color = self._DISABLED_CROSS
        painter.setPen(QtGui.QPen(color, 1.0, QtCore.Qt.PenStyle.DashLine))
        painter.drawLine(QtCore.QPointF(c.x() - r, c.y()),
                         QtCore.QPointF(c.x() + r, c.y()))
        painter.drawLine(QtCore.QPointF(c.x(), c.y() - r),
                         QtCore.QPointF(c.x(), c.y() + r))

    def _drawRimHighlight(self,
                          painter: QtGui.QPainter,
                          enabled: bool) -> None:
        '''Draw a bright arc across the upper-left rim to suggest a bevel.'''
        rect = self._limitRect()
        if enabled:
            color = self._padColor.lighter(165)
            color.setAlpha(180)
        else:
            color = self._DISABLED_RIM
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
        '''Draw the knob as a sphere.'''
        rect = self._knobRect()
        c = rect.center()
        r = rect.width() / 2.
        fx, fy = c.x() - 0.3 * r, c.y() - 0.3 * r
        grad = QtGui.QRadialGradient(c.x(), c.y(), r, fx, fy)
        if enabled:
            grad.setColorAt(0., self._knobColor.lighter(230))
            grad.setColorAt(1., self._knobColor.darker(155))
        else:
            grad.setColorAt(0., self._DISABLED_KNOB_LIGHT)
            grad.setColorAt(1., self._DISABLED_KNOB_DARK)
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
        '''Return the current fractional knob displacement.

        Returns
        -------
        numpy.ndarray
            Two-element array ``[fx, fy]`` in the range ``[-1, 1]``.
            ``fy`` is negated so that upward motion gives a positive value.
            Returns ``[0., 0.]`` when inactive.
        '''
        if self.active:
            displacement = QtCore.QLineF(self._center(), self.position)
            fx = max(-1., min(1.,  displacement.dx() / self.limit))
            fy = max(-1., min(1., -displacement.dy() / self.limit))
        else:
            fx, fy = 0., 0.
        return np.array([fx, fy])

    def _emitSignal(self) -> None:
        '''Emit :attr:`positionChanged` if the position changed.

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
