from PyQt5.QtWidgets import QDial
from PyQt5.QtCore import (pyqtSignal, pyqtSlot)
import numpy as np
import logging


logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)


class QRotaryEncoder(QDial):
    '''Subclassed QDial that emits signals indicating direction of rotation

    ...

    Inherits
    --------
    PyQt5.QtWidgets.QDial

    Properties
    ----------
    steps: int
        Number of steps in a complete turn of the dial.
        Default: 100

    Signals
    -------
    tick: int
        emitted each time the dial turns one step.
        +1: clockwise
        -1: counterclockwise

    '''

    tick = pyqtSignal(int)

    def __init__(self, *args, steps=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._steps = steps or 100
        self.setWrapping(True)
        self.setMinimum(0)
        self.setMaximum(self._steps - 1)
        self._value = self.value()
        self.valueChanged.connect(self.emitTick)

    @pyqtSlot(int)
    def emitTick(self, value):
        if value == self._value:
            return
        delta = value - self._value
        self._value = value
        direction = np.sign(delta)
        if np.abs(delta) > self.maximum() / 2:
            direction *= -1
        logger.debug(f'{value}: ' + 'up' if direction > 0 else 'down')
        self.tick.emit(direction)


if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    encoder = QRotaryEncoder()
    encoder.show()
    sys.exit(app.exec_())
