from QInstrument.lib import QInstrumentInterface
from QInstrument.instruments.Opus.Opus import Opus
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import pyqtSlot



class QOpusWidget(QInstrumentInterface):

    def __init__(self, *args, **kwargs):
        super().__init__(*args,
                         uiFile='OpusWidget.ui',
                         deviceClass=Opus,
                         **kwargs)
        self.connectSignals()

    def connectSignals(self):
        self.ui.PowerDial.valueChanged.connect(self.updatePower)
        self.ui.Power.editingFinished.connect(self.updatePowerDial)
        self.ui.PowerDial.valueChanged.connect(self.uncheck)
        self.ui.SendPower.clicked.connect(self.check)
        self.device.get_power.connect(self.updateActualPower)
	

    @pyqtSlot(int)
    def updatePower(self, value):
        self.ui.Power.setValue(value)

    @pyqtSlot()
    def check(self):
        self.ui.sentCheck.setChecked(True)

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
