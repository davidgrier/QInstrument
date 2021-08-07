from QInstrument.lib import QInstrument
from QInstrument import DS345


class QDS345(QInstrument):
    '''Stanford Research Systems DS345 Function Generator
    '''
    def __init__(self, **kwargs):
        super().__init__(uiFile='DS345Widget.ui',
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
    
