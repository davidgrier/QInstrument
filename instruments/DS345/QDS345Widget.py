from QInstrument.lib.QInstrumentWidget import QInstrumentWidget
from QInstrument.instruments.DS345.QDS345 import QDS345


class QDS345Widget(QInstrumentWidget):
    '''Stanford Research Systems DS345 Function Generator
    '''

    def __init__(self, *args, device=None, **kwargs):
        device = device or QDS345().find()
        super().__init__(*args,
                         uiFile='DS345Widget.ui',
                         device=device,
                         **kwargs)


def main():
    import sys
    from qtpy.QtWidgets import QApplication

    app = QApplication(sys.argv)
    widget = QDS345Widget()
    widget.show()
    sys.exit(app.exec())
