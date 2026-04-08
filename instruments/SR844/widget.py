from QInstrument.lib.QInstrumentWidget import QInstrumentWidget
from QInstrument.instruments.SR844.instrument import QSR844


class QSR844Widget(QInstrumentWidget):
    '''Stanford Research Systems SR844 RF Lock-in Amplifier
    '''

    UIFILE = 'SR844Widget.ui'
    INSTRUMENT = QSR844

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.adjustSize()


if __name__ == '__main__':
    QSR844Widget.example()

__all__ = ['QSR844Widget']
