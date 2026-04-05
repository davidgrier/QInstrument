from __future__ import annotations

import sys
from pathlib import Path
from qtpy import uic, QtCore, QtGui
from qtpy.QtWidgets import QWidget


class _SuppressArrowKeys(QtCore.QObject):
    '''Event filter that blocks Up and Down arrow key presses.

    Installed on the spinbox to prevent arrow keys from changing its
    value while the rotary encoder has focus.
    '''

    def eventFilter(self,
                    obj: QtCore.QObject,
                    event: QtCore.QEvent) -> bool:
        if event.type() == QtCore.QEvent.Type.KeyPress:
            if event.key() in (QtCore.Qt.Key.Key_Up,
                               QtCore.Qt.Key.Key_Down):
                return True
        return False


class QRotaryEncoderSpinBox(QWidget):
    '''QDoubleSpinBox controlled by a rotary encoder dial.

    Combines a :class:`QRotaryEncoder` dial and a ``QDoubleSpinBox``
    into a single widget.  Turning the dial steps the spinbox value up
    or down.  The spinbox background color interpolates between two
    colors as the value moves from minimum to maximum.

    Properties
    ==========
    colors : tuple[str, str]
        Background color interpolates from ``colors[0]`` at minimum to
        ``colors[1]`` at maximum.  Accepts any color string recognized
        by ``QColor`` (e.g. ``'white'``, ``'#68ff00'``).
        Default: ``('white', 'red')``.

    The following ``QDoubleSpinBox`` properties are delegated directly:

    ``decimals``, ``maximum``, ``minimum``, ``prefix``, ``singleStep``,
    ``stepType``, ``suffix``, ``value``, ``valueChanged``.
    '''

    def __init__(self, *args, colors: tuple[str, str] | None = None,
                 **kwargs) -> None:
        super().__init__(*args, **kwargs)
        uic.loadUi(Path(__file__).with_suffix('.ui'), self)
        self._spinbox = self.value  # save before _inheritMethods overwrites
        self._filter = _SuppressArrowKeys(self)
        self._spinbox.installEventFilter(self._filter)
        self._inheritMethods()
        self.setColors(colors or ('white', 'red'))
        self.encoder.setFocus()

    def _inheritMethods(self) -> None:
        '''Delegate QDoubleSpinBox methods to the embedded spinbox widget.'''
        for method in ('decimals', 'setDecimals',
                       'maximum', 'minimum',
                       'prefix', 'setPrefix',
                       'suffix', 'setSuffix',
                       'singleStep', 'setSingleStep',
                       'stepType', 'setStepType',
                       'value', 'setValue', 'valueChanged'):
            setattr(self, method, getattr(self._spinbox, method))

    def colors(self) -> tuple[str, str] | None:
        '''Return the current color pair, or ``None`` if disabled.'''
        return self._colors

    def setColors(self, colors: tuple[str, str] | None) -> None:
        '''Set the spinbox background color gradient.

        Idempotent: safe to call multiple times with the same or
        different colors without double-connecting the update slot.

        Parameters
        ----------
        colors : tuple[str, str] or None
            ``(low_color, high_color)`` pair, or ``None`` to disable
            color interpolation and disconnect the color-update slot.
        '''
        self._colors = colors
        try:
            self.valueChanged.disconnect(self._setColor)
        except (RuntimeError, TypeError):
            pass
        if colors is not None:
            self._c1 = QtGui.QColor(colors[0])
            self._c2 = QtGui.QColor(colors[1])
            self.valueChanged.connect(self._setColor)
            self._refreshColor()

    def setMinimum(self, value: float) -> None:
        '''Set the spinbox minimum and refresh the background color.'''
        self._spinbox.setMinimum(value)
        self._refreshColor()

    def setMaximum(self, value: float) -> None:
        '''Set the spinbox maximum and refresh the background color.'''
        self._spinbox.setMaximum(value)
        self._refreshColor()

    def setRange(self, minimum: float, maximum: float) -> None:
        '''Set the spinbox range and refresh the background color.'''
        self._spinbox.setRange(minimum, maximum)
        self._refreshColor()

    def _refreshColor(self) -> None:
        '''Repaint the spinbox background for the current value.'''
        if self._colors is not None:
            self._setColor(self.value())

    @QtCore.Slot(float)
    def _setColor(self, value: float) -> None:
        '''Update the spinbox background color for the current value.

        Parameters
        ----------
        value : float
            Current spinbox value, used to interpolate between the two
            endpoint colors.
        '''
        span = self.maximum() - self.minimum()
        if span == 0.:
            return
        f = (value - self.minimum()) / span
        r = (1. - f) * self._c1.redF()   + f * self._c2.redF()
        g = (1. - f) * self._c1.greenF() + f * self._c2.greenF()
        b = (1. - f) * self._c1.blueF()  + f * self._c2.blueF()
        color = QtGui.QColor.fromRgbF(r, g, b).name()
        style = (f'QDoubleSpinBox {{'
                 f' background-color: {color};'
                 f' selection-background-color: {color}; }}')
        self._spinbox.setStyleSheet(style)


def example() -> None:
    from qtpy.QtWidgets import QApplication

    app = QApplication.instance() or QApplication(sys.argv)
    widget = QRotaryEncoderSpinBox()
    widget.setRange(0., 5.)
    widget.setSingleStep(0.01)
    widget.setValue(0.)
    widget.setSuffix(' W')
    widget.setColors(('white', '#68ff00'))
    widget.show()
    sys.exit(app.exec())


__all__ = ['QRotaryEncoderSpinBox']


if __name__ == '__main__':
    example()
