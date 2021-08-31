from QInstrument.lib import QInstrumentInterface
from .DS345 import DS345


class QDS345(QInstrumentInterface):
    '''Stanford Research Systems DS345 Function Generator
    '''
    def __init__(self, *args, **kwargs):
        super().__init__(*args,
                         uiFile='DS345Widget.ui',
                         deviceClass=DS345,
                         **kwargs)


def main():
    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    widget = QDS345()
    widget.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
    
