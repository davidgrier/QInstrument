from QInstrument.lib import QInstrumentInterface
from QInstrument.instruments.SR830.SR830 import SR830


class QSR830(QInstrumentInterface):
    '''Stanford Research Systems SR830 Lockin Amplifier
    '''

    def __init__(self, *args, **kwargs):
        super().__init__(*args,
                         uiFile='SR830Widget.ui',
                         deviceClass=SR830,
                         **kwargs)


def main():
    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    widget = QSR830()
    widget.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
