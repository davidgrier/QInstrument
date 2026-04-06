from __future__ import annotations

import sys
from pathlib import Path
from qtpy import uic, QtCore, QtGui
from qtpy.QtWidgets import QWidget


class _SuppressArrowKeys(QtCore.QObject):
    '''Event filter that blocks Up and Down arrow key presses.

    Installed on the spinbox to prevent arrow keys from changing
    its value; the rotary encoder is the intended input device.
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

    Combines a :class:`QRotaryEncoder` dial and a
    ``QDoubleSpinBox`` into a single widget.  Turning the dial
    steps the spinbox value up or down.  The spinbox background
    color interpolates between two colors as the value moves from
    minimum to maximum.

    Parameters
    ----------
    colors : tuple[str, str] | None
        Background color interpolates from ``colors[0]`` at
        minimum to ``colors[1]`` at maximum.  Accepts any color
        string recognized by ``QColor`` (e.g. ``'white'``,
        ``'#68ff00'``).  Default: ``('white', 'red')``.

    The following ``QDoubleSpinBox`` methods are delegated
    directly:

    ``decimals``, ``setDecimals``, ``maximum``, ``minimum``,
    ``prefix``, ``setPrefix``, ``suffix``, ``setSuffix``,
    ``singleStep``, ``setSingleStep``, ``stepType``,
    ``setStepType``, ``value``, ``setValue``, ``valueChanged``.
    '''

    styleSheetUpdated = QtCore.Signal(str)

    def __init__(self,
                 *args,
                 colors: tuple[str, str] | None = None,
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
        '''Delegate QDoubleSpinBox methods to the spinbox.'''
        for method in ('decimals', 'setDecimals',
                       'maximum', 'minimum',
                       'prefix', 'setPrefix',
                       'suffix', 'setSuffix',
                       'singleStep', 'setSingleStep',
                       'stepType', 'setStepType',
                       'value', 'setValue', 'valueChanged'):
            setattr(self, method,
                    getattr(self._spinbox, method))

    def title(self) -> str:
        '''Return the title label text.'''
        return self.label.text()

    def setTitle(self, text: str) -> None:
        '''Set the title label text displayed above the spinbox.

        Parameters
        ----------
        text : str
            Label text.  Pass an empty string to hide the label.
        '''
        self.label.setText(text)

    def colors(self) -> tuple[str, str] | None:
        '''Return the current color pair, or ``None``.'''
        return self._colors

    def setColors(self,
                  colors: tuple[str, str] | None) -> None:
        '''Set the spinbox background color gradient.

        Idempotent: safe to call multiple times with the same or
        different colors without double-connecting the update slot.

        Parameters
        ----------
        colors : tuple[str, str] | None
            ``(low_color, high_color)`` pair, or ``None`` to
            disable color interpolation.
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
        '''Set the spinbox minimum and refresh the background.'''
        self._spinbox.setMinimum(value)
        self._refreshColor()

    def setMaximum(self, value: float) -> None:
        '''Set the spinbox maximum and refresh the background.'''
        self._spinbox.setMaximum(value)
        self._refreshColor()

    def setRange(self, minimum: float, maximum: float) -> None:
        '''Set the spinbox range and refresh the background.'''
        self._spinbox.setRange(minimum, maximum)
        self._refreshColor()

    def _refreshColor(self) -> None:
        '''Repaint the spinbox background for the current value.'''
        if self._colors is not None:
            self._setColor(self.value())

    @QtCore.Slot(float)
    def _setColor(self, value: float) -> None:
        '''Update the spinbox background color for *value*.

        Parameters
        ----------
        value : float
            Current spinbox value, used to interpolate between
            the two endpoint colors.
        '''
        span = self.maximum() - self.minimum()
        if span == 0.:
            return
        f = (value - self.minimum()) / span
        r = (1.-f) * self._c1.redF()   + f * self._c2.redF()
        g = (1.-f) * self._c1.greenF() + f * self._c2.greenF()
        b = (1.-f) * self._c1.blueF()  + f * self._c2.blueF()
        color = QtGui.QColor.fromRgbF(r, g, b).name()
        style = (f'QDoubleSpinBox {{'
                 f' background-color: {color};'
                 f' selection-background-color: {color}; }}')
        self._spinbox.setStyleSheet(style)
        self.styleSheetUpdated.emit(style)

    @classmethod
    def example(cls) -> None:
        '''Display the widget with laser-power defaults.'''
        from qtpy.QtWidgets import QApplication
        app = (QApplication.instance() or
               QApplication(sys.argv))
        widget = cls()
        widget.setRange(0., 5.)
        widget.setSingleStep(0.01)
        widget.setValue(0.)
        widget.setSuffix(' W')
        widget.setColors(('white', '#68ff00'))
        widget.show()
        sys.exit(app.exec())


__all__ = ['QRotaryEncoderSpinBox']


if __name__ == '__main__':
    QRotaryEncoderSpinBox.example()
