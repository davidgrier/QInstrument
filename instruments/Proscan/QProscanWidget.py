from QInstrument.lib import QInstrumentWidget
from QInstrument.instruments.Proscan.QProscan import QProscan
from PyQt5.QtCore import (pyqtSlot, QTimer)
import logging


logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class QProscanWidget(QInstrumentWidget):
    '''Prior Proscan Microscope Controller
    '''

    def __init__(self, *args, interval=None, **kwargs):
        device = QProscan().find()
        super().__init__(*args,
                         uiFile='ProscanWidget.ui',
                         device=device,
                         **kwargs)
        self.ui.joystick.fullscale = 200.  # um/s
        self.interval = interval or 200    # ms
        self.timer = QTimer()
        self.connectSignals()
        self._zvalue = self.ui.z.value()

    def connectSignals(self):
        self.device.dataReady.connect(self.updatePosition)
        self.timer.timeout.connect(self.poll)
        self.ui.joystick.positionChanged.connect(self.updateVelocity)
        self.ui.zdial.stepUp.connect(self.device.stepUp)
        self.ui.zdial.stepDown.connect(self.device.stepDown)

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
        self.ui.x.display(x)
        self.ui.y.display(y)
        self.ui.z.display(z)

    @pyqtSlot(object)
    def updateVelocity(self, velocity):
        logger.debug(f'velocity: {velocity}')
        self.device.set_velocity(velocity)


def main():
    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    widget = QProscan()  # .startPolling()
    widget.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
