from QInstrument.lib import QInstrumentWidget
from QInstrument.instruments.DS345.QDS345 import QDS345


class QDS345Widget(QInstrumentWidget):
    '''Stanford Research Systems DS345 Function Generator
    '''

    def __init__(self, *args, **kwargs):
        super().__init__(*args,
                         uiFile='DS345Widget.ui',
                         deviceClass=QDS345,
                         **kwargs)


def main():
    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    widget = QDS345Widget()
    widget.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
