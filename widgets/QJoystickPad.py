from __future__ import annotations

import sys
import logging
import numpy as np
from qtpy import QtWidgets, QtGui, QtCore

from QInstrument.widgets.QJoystick import QJoystick


logger = logging.getLogger(__name__)


class QTriangleButton(QtWidgets.QAbstractButton):
    '''Push-button that paints a filled equilateral-ish triangle.

    The triangle points in the given direction.  Visual state
    (hover, pressed, disabled) is rendered automatically.

    Parameters
    ----------
    direction : str
        One of ``'up'``, ``'down'``, ``'left'``, ``'right'``.
    '''

    # Normalised (x, y) vertices for each direction, within [0, 1]^2.
    _VERTICES: dict[str, list[tuple[float, float]]] = {
        'up':    [(0.5, 0.0), (0.0, 1.0), (1.0, 1.0)],
        'down':  [(0.5, 1.0), (0.0, 0.0), (1.0, 0.0)],
        'left':  [(0.0, 0.5), (1.0, 0.0), (1.0, 1.0)],
        'right': [(1.0, 0.5), (0.0, 0.0), (0.0, 1.0)],
    }

    _DISABLED_COLOR  = QtGui.QColor(192, 192, 192)
    _DISABLED_BORDER = QtGui.QColor(144, 144, 144)

    def __init__(self, direction: str, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._direction = direction
        self._color = QtGui.QColor('#a888c8')
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_Hover, True)

    def _getColor(self) -> QtGui.QColor:
        return self._color

    def _setColor(self, color: QtGui.QColor) -> None:
        self._color = color
        self.update()

    color = QtCore.Property(QtGui.QColor, _getColor, _setColor)

    def setColor(self, color: QtGui.QColor) -> None:
        '''Set the button fill color and repaint.

        Parameters
        ----------
        color : QtGui.QColor
            Base fill color; pressed and border shades are derived
            automatically.
        '''
        self._setColor(color)

    def sizeHint(self) -> QtCore.QSize:
        '''Return the preferred button size.'''
        return QtCore.QSize(30, 30)

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        '''Paint the triangle, reflecting enabled/hover/pressed state.'''
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing, True)
        pad = 4
        w = self.width()  - 2 * pad
        h = self.height() - 2 * pad
        vertices = self._VERTICES[self._direction]
        path = QtGui.QPainterPath()
        x0, y0 = vertices[0]
        path.moveTo(pad + w * x0, pad + h * y0)
        for vx, vy in vertices[1:]:
            path.lineTo(pad + w * vx, pad + h * vy)
        path.closeSubpath()
        if not self.isEnabled():
            fill   = self._DISABLED_COLOR
            border = self._DISABLED_BORDER
        elif self.isDown():
            fill   = self._color.darker(140)
            border = self._color.darker(160)
        elif self.underMouse():
            fill   = self._color.lighter(120)
            border = self._color.darker(130)
        else:
            fill   = self._color
            border = self._color.darker(140)
        painter.setPen(QtGui.QPen(border, 1.5))
        painter.setBrush(QtGui.QBrush(fill))
        painter.drawPath(path)


class QJoystickPad(QtWidgets.QWidget):
    '''QJoystick with four directional step buttons.

    Arranges a :class:`QJoystick` in the center of a 3×3 grid with a
    triangular step button on each side.  The central joystick works
    normally.  Each step button, when pressed, emits
    :attr:`positionChanged` once at ``stepFraction`` of the axis
    full-scale; releasing the button emits zero velocity.

    Signals
    -------
    positionChanged(numpy.ndarray)
        Forwarded from the embedded joystick, and also emitted by the
        step buttons.  Carries a two-element ``[vx, vy]`` array in the
        same output range as the joystick.

    Properties
    ==========
    stepFraction : float
        Fraction of full-scale used by the step buttons.
        Range ``(0, 1]``, default 0.25.
        Settable via stylesheet: ``qproperty-stepFraction: 0.5;``
    padColor : QtGui.QColor
        Forwarded to the embedded joystick and the step buttons.
        Settable via stylesheet: ``qproperty-padColor: #rrggbb;``
    knobColor : QtGui.QColor
        Forwarded to the embedded joystick.
        Settable via stylesheet: ``qproperty-knobColor: #rrggbb;``
    '''

    positionChanged = QtCore.Signal(object)

    _BUTTON_SIZE = 24   # px; fixed size of each triangular step button

    # Unit step vectors (fx, fy) in joystick fraction space [-1, 1]^2.
    _STEP_VECTORS: dict[str, tuple[float, float]] = {
        'left':  (-1.,  0.),
        'right': ( 1.,  0.),
        'up':    ( 0.,  1.),
        'down':  ( 0., -1.),
    }

    def __init__(self, *args,
                 fullscale: float | None = None,
                 stepFraction: float = 0.25,
                 **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._stepFraction = float(stepFraction)
        self._setupUi(fullscale)

    def _setupUi(self, fullscale: float | None) -> None:
        self.joystick = QJoystick(fullscale=fullscale, parent=self)
        self.joystick.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Expanding)
        self.joystick.positionChanged.connect(self.positionChanged)

        self._buttons: dict[str, QTriangleButton] = {}
        for direction in ('up', 'down', 'left', 'right'):
            btn = QTriangleButton(direction, parent=self)
            btn.setFixedSize(self._BUTTON_SIZE, self._BUTTON_SIZE)
            btn.pressed.connect(
                lambda d=direction: self._onPressed(d))
            btn.released.connect(self._onReleased)
            self._buttons[direction] = btn

        layout = QtWidgets.QGridLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        AlignHCenter = QtCore.Qt.AlignmentFlag.AlignHCenter
        AlignVCenter = QtCore.Qt.AlignmentFlag.AlignVCenter
        layout.addWidget(self._buttons['up'],    0, 1,
                         alignment=AlignHCenter)
        layout.addWidget(self._buttons['left'],  1, 0,
                         alignment=AlignVCenter)
        layout.addWidget(self.joystick,          1, 1)
        layout.addWidget(self._buttons['right'], 1, 2,
                         alignment=AlignVCenter)
        layout.addWidget(self._buttons['down'],  2, 1,
                         alignment=AlignHCenter)
        layout.setRowStretch(1, 1)
        layout.setColumnStretch(1, 1)

        self._syncButtonColors()

    def hasHeightForWidth(self) -> bool:
        '''Report that this widget maintains a 1:1 aspect ratio.'''
        return True

    def heightForWidth(self, width: int) -> int:
        '''Return *width*, enforcing a square allocation.'''
        return width

    def sizeHint(self) -> QtCore.QSize:
        '''Return the preferred widget size with a 1:1 aspect ratio.'''
        lyt = self.layout()
        m   = lyt.contentsMargins()
        s   = lyt.spacing()
        b   = self._BUTTON_SIZE
        j   = self.joystick.sizeHint().width()
        side = m.left() + b + s + j + s + b + m.right()
        return QtCore.QSize(side, side)

    def _syncButtonColors(self) -> None:
        color = self.joystick.padColor
        for btn in self._buttons.values():
            btn.setColor(color)

    # ------------------------------------------------------------------
    # Step button slots
    # ------------------------------------------------------------------

    @QtCore.Slot()
    def _onPressed(self, direction: str) -> None:
        '''Emit step velocity for *direction* and deflect the knob.'''
        fx, fy = self._STEP_VECTORS[direction]
        fracs  = np.array([fx, fy]) * self._stepFraction
        lo, hi = self.joystick.minimum(), self.joystick.maximum()
        values = lo + (fracs + 1.) / 2. * (hi - lo)
        self.joystick.setKnobFraction(fx * self._stepFraction,
                                      fy * self._stepFraction)
        self.positionChanged.emit(values)

    @QtCore.Slot()
    def _onReleased(self) -> None:
        '''Return the knob to centre and emit zero velocity.'''
        self.joystick.setKnobFraction(0., 0.)
        lo, hi = self.joystick.minimum(), self.joystick.maximum()
        self.positionChanged.emit(np.full(2, (lo + hi) / 2.))

    # ------------------------------------------------------------------
    # stepFraction property
    # ------------------------------------------------------------------

    def _getStepFraction(self) -> float:
        return self._stepFraction

    def _setStepFraction(self, value: float) -> None:
        self._stepFraction = float(value)

    stepFraction = QtCore.Property(
        float, _getStepFraction, _setStepFraction)

    def setStepFraction(self, value: float) -> None:
        '''Set the step-button velocity fraction.

        Parameters
        ----------
        value : float
            Fraction of full-scale in the range ``(0, 1]``.
        '''
        self._setStepFraction(value)

    # ------------------------------------------------------------------
    # padColor / knobColor — forwarded to joystick and buttons
    # ------------------------------------------------------------------

    def _getPadColor(self) -> QtGui.QColor:
        return self.joystick.padColor

    def _setPadColor(self, color: QtGui.QColor) -> None:
        self.joystick.padColor = color
        for btn in self._buttons.values():
            btn.setColor(color)

    padColor = QtCore.Property(QtGui.QColor, _getPadColor, _setPadColor)

    def setPadColor(self, color: QtGui.QColor) -> None:
        '''Set the pad and step-button color.

        Parameters
        ----------
        color : QtGui.QColor
            Base color forwarded to the joystick pad and all four
            step buttons.
        '''
        self._setPadColor(color)

    def _getKnobColor(self) -> QtGui.QColor:
        return self.joystick.knobColor

    def _setKnobColor(self, color: QtGui.QColor) -> None:
        self.joystick.knobColor = color

    knobColor = QtCore.Property(QtGui.QColor, _getKnobColor, _setKnobColor)

    def setKnobColor(self, color: QtGui.QColor) -> None:
        '''Set the joystick knob color.

        Parameters
        ----------
        color : QtGui.QColor
            Base color forwarded to the embedded joystick knob.
        '''
        self._setKnobColor(color)

    # ------------------------------------------------------------------
    # Range proxies
    # ------------------------------------------------------------------

    def setRange(self, minimum: float, maximum: float) -> None:
        '''Set the joystick output range for both axes.

        Parameters
        ----------
        minimum : float
            Output value at full negative deflection.
        maximum : float
            Output value at full positive deflection.
        '''
        self.joystick.setRange(minimum, maximum)

    def minimum(self) -> float:
        '''Return the output value at full negative deflection.'''
        return self.joystick.minimum()

    def maximum(self) -> float:
        '''Return the output value at full positive deflection.'''
        return self.joystick.maximum()

    def _getFullscale(self) -> float:
        return self.joystick.fullscale

    def _setFullscale(self, value: float) -> None:
        self.joystick.fullscale = value

    fullscale = QtCore.Property(float, _getFullscale, _setFullscale)


def example() -> None:
    from qtpy.QtWidgets import QApplication

    def report(xy: np.ndarray) -> None:
        print('velocity: ({:+.2f}, {:+.2f})'.format(*xy), end='\r')

    app = QApplication.instance() or QApplication(sys.argv)
    pad = QJoystickPad(fullscale=200.)
    pad.positionChanged.connect(report)
    pad.show()
    sys.exit(app.exec())


__all__ = ['QJoystickPad', 'QTriangleButton']


if __name__ == '__main__':
    example()
