from QInstrument.lib.QInstrumentTree import QInstrumentTree
from QInstrument.instruments.StanfordResearch.SR844.instrument import QSR844


class QSR844Tree(QInstrumentTree):
    '''Parameter tree for the Stanford Research SR844 RF lock-in amplifier.'''

    INSTRUMENT = QSR844


if __name__ == '__main__':
    QSR844Tree.example()

__all__ = ['QSR844Tree']
