from PyQt5 import uic
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import pyqtSlot


class QOpusWidget(QWidget):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ui = self._loadUi('QOpusWidget.ui')
        self._connectSignals()

    def _loadUi(self, uifile):
        form, _ = uic.loadUiType(uifile)
        ui = form()
        ui.setupUi(self)
        return ui

    def _connectSignals(self):
        self.ui.powerDial.valueChanged.connect(self.updatePower)
        self.ui.power.editingFinished.connect(self.updatePowerDial)

    @pyqtSlot(int)
    def updatePower(self, value):
        self.ui.power.setValue(value/100.)

    @pyqtSlot()
    def updatePowerDial(self):
        value = self.ui.power.value()
        self.ui.powerDial.setValue(int(value*100))


if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    widget = QOpusWidget()
    widget.show()
    sys.exit(app.exec_())

    
