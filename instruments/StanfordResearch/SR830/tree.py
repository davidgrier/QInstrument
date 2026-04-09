from QInstrument.lib.QInstrumentTree import QInstrumentTree
from QInstrument.instruments.StanfordResearch.SR830.instrument import QSR830


class QSR830Tree(QInstrumentTree):
    '''Parameter tree for the Stanford Research Systems SR830 Lock-in Amplifier.'''

    INSTRUMENT = QSR830


if __name__ == '__main__':
    QSR830Tree.example()

__all__ = ['QSR830Tree']
