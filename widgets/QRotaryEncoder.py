import sys
import logging
from qtpy import QtCore
from qtpy.QtWidgets import QDial
import numpy as np


logger = logging.getLogger(__name__)


class QRotaryEncoder(QDial):
    '''QDial subclass that emits directional step signals.

    Wraps the full dial range and emits :attr:`stepUp` or
    :attr:`stepDown` each time the user turns the dial by one step,
    correctly handling wrap-around.

    Properties
    ==========
    steps : int
        Number of discrete steps in one full turn. Default: 100.

    Signals
    -------
    stepUp
        Emitted each time the dial turns one step clockwise.
    stepDown
        Emitted each time the dial turns one step counter-clockwise.
    '''

    stepUp = QtCore.Signal()
    stepDown = QtCore.Signal()

    def __init__(self, *args, steps: int | None = None, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.setWrapping(True)
        self.setMinimum(0)
        self.setSteps(steps or 100)
        self._value = self.value()
        self.valueChanged.connect(self._emitTick)

    @QtCore.Slot(int)
    def _emitTick(self, value: int) -> None:
        '''Emit :attr:`stepUp` or :attr:`stepDown` based on dial movement.

        Detects wrap-around by checking whether the raw delta exceeds
        half the dial range, and inverts the direction accordingly.

        Parameters
        ----------
        value : int
            New dial value emitted by ``valueChanged``.
        '''
        if value == self._value:
            return
        delta = value - self._value
        self._value = value
        direction = int(np.sign(delta))
        if np.abs(delta) > self.maximum() / 2:
            direction *= -1
        if direction > 0:
            self.stepUp.emit()
            logger.debug(f'{value}: up')
        else:
            self.stepDown.emit()
            logger.debug(f'{value}: down')

    def setSteps(self, value: int) -> None:
        '''Set the number of steps in one full turn.

        Parameters
        ----------
        value : int
            Number of discrete steps.  Sets the dial maximum to
            ``value - 1`` so that the range is ``[0, value - 1]``.
        '''
        self._steps = int(value)
        self.setMaximum(self._steps - 1)

    def steps(self) -> int:
        '''Return the number of steps in one full turn.'''
        return self._steps


def example() -> None:
    from qtpy.QtWidgets import QApplication

    def report(value: int) -> None:
        print(f'value = {value:03d}', end='\r')

    app = QApplication.instance() or QApplication(sys.argv)
    encoder = QRotaryEncoder(steps=200)
    encoder.valueChanged.connect(report)
    encoder.show()
    sys.exit(app.exec())


__all__ = ['QRotaryEncoder']


if __name__ == '__main__':
    example()
