from QInstrument.lib import QInstrumentInterface
from QInstrument.instruments import Proscan
from PyQt5.QtCore import pyqtSlot


class QProscan(QInstrumentInterface):
    '''Prior Proscan Microscope Controller
    '''

    def __init__(self, **kwargs):
        super().__init__(uiFile='ProscanWidget.ui',
                         deviceClass=Proscan,
                         **kwargs)
        self.connectSignals()

    def connectSignals(self):
        if self.device.isOpen():
            self.device.dataReady.connect(self.updatePosition)

    @pyqtSlot(str)
    def updatePosition(self, data):
        print(data)
        x, y, z = list(map(int, data.strip().split(',')))
        
def main():
    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    widget = QProscan()
    widget.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
