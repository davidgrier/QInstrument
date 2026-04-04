from QInstrument.lib.QInstrumentWidget import QInstrumentWidget
from QInstrument.instruments.PiezoDrive.instrument import QPDUS210
from PyQt5.QtCore import (pyqtProperty, pyqtSlot, QTimer)


class QPDUS210Widget(QInstrumentWidget):
    '''PiezoDrive 210 Ultrasonic Amplifier
    '''

    UIFILE = 'PDUS210Widget.ui'

    def __init__(self, *args, **kwargs):
        device = QPDUS210().find()
        super().__init__(*args, device=device, **kwargs)
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


if __name__ == '__main__':
    QPDUS210Widget.example()

__all__ = ['QPDUS210Widget']
