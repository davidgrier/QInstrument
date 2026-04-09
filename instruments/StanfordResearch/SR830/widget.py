from QInstrument.lib.QInstrumentWidget import QInstrumentWidget
from QInstrument.instruments.StanfordResearch.SR830.instrument import QSR830


class QSR830Widget(QInstrumentWidget):
    '''Stanford Research Systems SR830 Lock-in Amplifier
    '''

    UIFILE = 'SR830Widget.ui'
    INSTRUMENT = QSR830


if __name__ == '__main__':
    QSR830Widget.example()

__all__ = ['QSR830Widget']
