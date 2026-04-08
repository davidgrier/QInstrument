from QInstrument.lib.QInstrumentTree import QInstrumentTree
from QInstrument.instruments.SR844.instrument import QSR844


class QSR844Tree(QInstrumentTree):
    '''Parameter tree for the Stanford Research Systems SR844 RF Lock-in Amplifier.'''

    INSTRUMENT = QSR844


if __name__ == '__main__':
    QSR844Tree.example()

__all__ = ['QSR844Tree']
