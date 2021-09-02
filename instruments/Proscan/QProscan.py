from QInstrument.lib import QInstrumentInterface
from QInstrument.instruments.Proscan.Proscan import Proscan
from PyQt5.QtCore import (pyqtSlot, QTimer)
import numpy as np
import logging

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class QProscan(QInstrumentInterface):
    '''Prior Proscan Microscope Controller
    '''

    def __init__(self, *args, interval=None, **kwargs):
        super().__init__(*args,
                         uiFile='ProscanWidget.ui',
                         deviceClass=Proscan,
                         **kwargs)
        self.ui.joystick.fullscale = 200.  # um/s
        self.interval = interval or 200   # ms
        self.timer = QTimer()
        self.connectSignals()
        self._zvalue = self.ui.zdial.value()

    def connectSignals(self):
        self.device.dataReady.connect(self.updatePosition)
        self.timer.timeout.connect(self.poll)
        self.ui.joystick.positionChanged.connect(self.updateVelocity)
        self.ui.zdial.valueChanged.connect(self.stepFocus)

    def startPolling(self):
        if self.isEnabled():
            self.timer.start(self.interval)
        return self

    def stopPolling(self):
        self.timer.stop()

    @pyqtSlot()
    def poll(self):
        self.device.send('P')

    @pyqtSlot(str)
    def updatePosition(self, data):
        try:
            x, y, z = list(map(int, data.strip().split(',')))
        except ValueError:
            return
        self.ui.x.display(x)
        self.ui.y.display(y)
        self.ui.z.display(z)

    @pyqtSlot(object)
    def updateVelocity(self, velocity):
        logger.debug(f'velocity: {velocity}')
        self.device.set_velocity(velocity)

    @pyqtSlot(int)
    def stepFocus(self, zvalue):
        if zvalue == self._zvalue:
            return
        delta = zvalue - self._zvalue
        direction = np.sign(delta)
        if np.abs(delta) > self.ui.zdial.maximum() / 2:
            direction *= -1
        if direction > 0:
            logger.debug(f'{zvalue} step up')
        else:
            logger.debug(f'{zvalue} step down')
        self._zvalue = zvalue


def main():
    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    widget = QProscan()  # .startPolling()
    widget.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
