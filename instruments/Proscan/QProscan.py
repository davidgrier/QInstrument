from QInstrument.lib import QInstrumentInterface
from QInstrument.instruments import Proscan


class QProscan(QInstrumentInterface):
    '''Prior Proscan Microscope Controller
    '''

    def __init__(self, **kwargs):
        super().__init__(uiFile='ProscanWidget.ui',
                         deviceClass=Proscan,
                         **kwargs)


def main():
    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    widget = QProscan()
    widget.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
