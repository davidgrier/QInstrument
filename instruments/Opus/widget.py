from QInstrument.lib.QInstrumentWidget import QInstrumentWidget
from QInstrument.instruments.Opus.instrument import QOpus
from PyQt5.QtCore import (pyqtSlot, QTimer)
import logging


logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class QOpusWidget(QInstrumentWidget):

    UIFILE = 'OpusWidget.ui'

    def __init__(self, *args, interval=None, **kwargs):
        device = QOpus().find()
        super().__init__(*args, device=device, **kwargs)
        self.interval = interval or 200
        self.timer = QTimer()
        self.connectSignals()
        self.startPolling()

    def connectSignals(self):
        self.timer.timeout.connect(self.poll)
        self.PowerDial.valueChanged.connect(self.updatePower)
        self.Power.editingFinished.connect(self.updatePowerDial)
        self.PowerDial.valueChanged.connect(self.uncheck)
        self.SendPower.clicked.connect(self.check)
        self.device.dataReady.connect(self.updateValues)
        self.Disable.clicked.connect(self.disable)

    def startPolling(self):
        if self.isEnabled():
            self.timer.start(self.interval)
        return self

    def stopPolling(self):
        self.timer.stop()

    @pyqtSlot()
    def poll(self):
        self.device.transmit('POWER?')
        self.device.transmit('CURRENT?')
        self.device.transmit('STATUS?')

    @pyqtSlot(int)
    def updatePower(self, value):
        self.Power.setValue(value)

    @pyqtSlot(str)
    def updateValues(self, data):

        if 'mW' in data:
            numeric_filter = filter(str.isdigit, data)
            p = float((int("".join(numeric_filter))/10))
            if p == 0.0:
                self.EnableSwitch.setChecked(False)
            if p != 0.0:
                self.EnableSwitch.setChecked(True)
            self.ActualPower.setValue(p)
        if '%' in data:
            numeric_filter = filter(str.isdigit, data)
            p = float((int("".join(numeric_filter))/10))
            self.CurrentBox.setValue(p)

    @pyqtSlot()
    def check(self):
        self.sentCheck.setChecked(True)
        a = self.Power.value()
        self.device.set_power(a)

    @pyqtSlot()
    def uncheck(self):
        self.sentCheck.setChecked(False)

    @pyqtSlot()
    def updatePowerDial(self):
        value = self.Power.value()
        self.PowerDial.setValue(int(value))

    def disable(self):
        self.device.transmit('OFF')


if __name__ == '__main__':
    QOpusWidget.example()

__all__ = ['QOpusWidget']
