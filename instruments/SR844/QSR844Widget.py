from QInstrument.lib import QInstrumentWidget
from QInstrument.instruments.SR844.QSR844 import QSR844


class QSR844Widget(QInstrumentWidget):
    '''Stanford Research Systems SR844 Lockin Amplifier
    '''

    def __init__(self, *args, device=None, **kwargs):
        device = device or QSR844().find()
        super().__init__(*args,
                         uiFile='SR844Widget.ui',
                         device=device,
                         **kwargs)


def main():
    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    widget = QSR844Widget()
    widget.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
