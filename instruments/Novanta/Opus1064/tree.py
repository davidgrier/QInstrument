from QInstrument.lib.QInstrumentTree import QInstrumentTree
from QInstrument.instruments.Novanta.Opus1064.instrument import QOpus1064


class QOpus1064Tree(QInstrumentTree):
    '''Parameter tree for a Novanta Opus1064 laser.'''

    INSTRUMENT = QOpus1064


if __name__ == '__main__':
    QOpus1064Tree.example()

__all__ = ['QOpus1064Tree']
