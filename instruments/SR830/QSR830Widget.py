from QInstrument.lib import QInstrumentWidget
from QInstrument.instruments.SR830.QSR830 import QSR830


class QSR830Widget(QInstrumentWidget):
    '''Stanford Research Systems SR830 Lockin Amplifier
    '''

    def __init__(self, *args, device=None, **kwargs):
        device = device or QSR830().find()
        super().__init__(*args,
                         uiFile='SR830Widget.ui',
                         device=device,
                         **kwargs)


def main():
    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    widget = QSR830Widget()
    widget.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
