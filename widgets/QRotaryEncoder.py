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
    stepUp:
        emitted each time the dial turns one step clockwise
    stepDown:
        emitted each time the dial turns one step counterclockwise
    '''

    stepUp = pyqtSignal()
    stepDown = pyqtSignal()

    def __init__(self, *args, steps=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWrapping(True)
        self.setMinimum(0)
        self.setSteps(steps or 100)
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
        if direction > 0:
            self.stepUp.emit()
        else:
            self.stepDown.emit()
        logger.debug(f'{value}: ' + 'up' if direction > 0 else 'down')

    def setSteps(self, value):
        self._steps = int(value)
        self.setMaximum(self._steps - 1)

    def steps(self):
        return self._steps


if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    encoder = QRotaryEncoder()
    encoder.show()
    sys.exit(app.exec_())
