from QInstrument.lib import QInstrumentInterface
from QInstrument.instruments.PiezoDrive.PDUS210 import PDUS210
from PyQt5.QtCore import (pyqtProperty, pyqtSlot, QTimer)


class QPDS210(QInstrumentInterface):
    '''PiezoDrive 210 Ultrasonic Amplifier
    '''

    def __init__(self, *args, **kwargs):
        super().__init__(*args,
                         uiFile='PDUS210Widget.ui',
                         deviceClass=PDUS210,
                         **kwargs)
        self.setupTimer()
        self.interval = 0.2

    def setupTimer(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.poll)
        self.start = self.timer.start
        self.stop = self.timer.stop

    @pyqtSlot()
    def poll(self):
        for p in ['current', 'voltage', 'frequency', 'impedance', 'phase',
                  'loadPower', 'amplifierPower', 'temperature',
                  'targetCurrent']:
            self.set(p)

    @pyqtProperty(int)
    def interval(self):
        return self.timer.interval()

    @interval.setter
    def interval(self, interval):
        self.time.setInterval(interval)


def main():
    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    widget = QPDS210()
    widget.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
