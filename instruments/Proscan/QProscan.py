from QInstrument.lib import QInstrumentInterface
from QInstrument.instruments import Proscan
from PyQt5.QtCore import (pyqtSlot, QTimer)


class QProscan(QInstrumentInterface):
    '''Prior Proscan Microscope Controller
    '''

    def __init__(self, interval=None, **kwargs):
        super().__init__(uiFile='ProscanWidget.ui',
                         deviceClass=Proscan,
                         **kwargs)
        self.interval = interval or 200
        self.timer = QTimer()
        self.connectSignals()

    def connectSignals(self):
        self.device.dataReady.connect(self.updatePosition)
        self.timer.timeout.connect(self.poll)

    def start(self):
        if self.isEnabled():
            self.timer.start(self.interval)

    def stop(self):
        self.timer.stop()
        
    @pyqtSlot()
    def poll(self):
        self.device.send('P')

    @pyqtSlot(str)
    def updatePosition(self, data):
        x, y, z = list(map(int, data.strip().split(',')))
        self.ui.x.setValue(x)
        self.ui.y.setValue(y)
        self.ui.z.setValue(z)
        
def main():
    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    widget = QProscan()
    widget.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
