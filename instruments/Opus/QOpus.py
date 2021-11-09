from QInstrument.lib import QInstrumentInterface
from QInstrument.instruments.Opus.Opus import Opus
from PyQt5.QtCore import (pyqtSlot, QTimer)
import logging

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class QOpusWidget(QInstrumentInterface):

    def __init__(self, *args, interval=None, **kwargs):
        super().__init__(*args,
                         uiFile='OpusWidget.ui',
                         deviceClass=Opus,
                         **kwargs)
        self.interval = interval or 200
        self.timer = QTimer()
        self.connectSignals()
        self.startPolling()

    def connectSignals(self):
        self.timer.timeout.connect(self.poll)
        self.ui.PowerDial.valueChanged.connect(self.updatePower)
        self.ui.Power.editingFinished.connect(self.updatePowerDial)
        self.ui.PowerDial.valueChanged.connect(self.uncheck)
        self.ui.SendPower.clicked.connect(self.check)
        self.device.dataReady.connect(self.updateActualPower)
	
    def startPolling(self):
        if self.isEnabled():
            self.timer.start(self.interval)
        return self

    def stopPolling(self):
        self.timer.stop()
	
    @pyqtSlot()
    def poll(self):
        self.device.send('POWER?')
        self.device.send('CURRENT?')
        self.device.send('STATUS?')
	
    @pyqtSlot(int)
    def updatePower(self, value):
        self.ui.Power.setValue(value)
	
    @pyqtSlot(str)
    def updateActualPower(self, data):
        if 'mW' in data:
            numeric_filter = filter(str.isdigit, data)
                if numeric_filter == 0000:
                    self.ui.EnableSwitch.setChecked(False)
                else:
                    self.ui.EnableSwitch.setChecked(Talse)
            p = float((int("".join(numeric_filter))/10))
            self.ui.ActualPower.setValue(p)
        if '%' in data:
            numeric_filter = filter(str.isdigit, data)
            p = float((int("".join(numeric_filter))/10))
            self.ui.CurrentBox.setValue(p)
        if 'ENABLED' in data:
            self.ui.Keyswitch.setChecked(True)
        if 'DISABLED' in data:
            self.ui.Keyswitch.setChecked(False)

    @pyqtSlot()
    def check(self):
        self.ui.sentCheck.setChecked(True)
        a = self.ui.Power.value()
        self.device.set_power(a)

    @pyqtSlot()
    def uncheck(self):
        self.ui.sentCheck.setChecked(False)

    @pyqtSlot()
    def updatePowerDial(self):
        value = self.ui.Power.value()
        self.ui.PowerDial.setValue(int(value))

def main():
    import sys
    from PyQt5.QtWidgets import QApplication


    app = QApplication(sys.argv)
    widget = QOpusWidget()
    widget.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
