from QInstrument.lib.QInstrumentWidget import QInstrumentWidget
from QInstrument.instruments.Proscan.instrument import QProscan
from PyQt5.QtCore import (pyqtSlot, QTimer)
import logging


logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class QProscanWidget(QInstrumentWidget):
    '''Prior Proscan Microscope Controller
    '''

    UIFILE = 'ProscanWidget.ui'

    def __init__(self, *args, interval=None, **kwargs):
        device = QProscan().find()
        super().__init__(*args, device=device, **kwargs)
        self.joystick.fullscale = 200.  # um/s
        self.interval = interval or 200    # ms
        self.timer = QTimer()
        self.connectSignals()
        self._zvalue = self.z.value()

    def connectSignals(self):
        self.device.dataReady.connect(self.updatePosition)
        self.timer.timeout.connect(self.poll)
        self.joystick.positionChanged.connect(self.updateVelocity)
        self.zdial.stepUp.connect(self.device.stepUp)
        self.zdial.stepDown.connect(self.device.stepDown)

    def startPolling(self):
        if self.isEnabled():
            self.timer.start(self.interval)
        return self

    def stopPolling(self):
        self.timer.stop()

    @pyqtSlot()
    def poll(self):
        self.device.transmit('P')

    @pyqtSlot(str)
    def updatePosition(self, data):
        try:
            x, y, z = list(map(int, data.strip().split(',')))
        except ValueError:
            return
        self.x.display(x)
        self.y.display(y)
        self.z.display(z)

    @pyqtSlot(object)
    def updateVelocity(self, velocity):
        logger.debug(f'velocity: {velocity}')
        self.device.set_velocity(velocity)


if __name__ == '__main__':
    QProscanWidget.example()

__all__ = ['QProscanWidget']
