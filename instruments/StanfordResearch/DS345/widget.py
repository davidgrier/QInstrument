from QInstrument.lib.QInstrumentWidget import QInstrumentWidget
from QInstrument.instruments.StanfordResearch.DS345.instrument import QDS345


class QDS345Widget(QInstrumentWidget):
    '''Stanford Research Systems DS345 Function Generator
    '''

    UIFILE = 'DS345Widget.ui'
    INSTRUMENT = QDS345

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.adjustSize()


if __name__ == '__main__':
    QDS345Widget.example()

__all__ = ['QDS345Widget']
