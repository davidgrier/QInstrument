from QInstrument.lib.QInstrumentTree import QInstrumentTree
from QInstrument.instruments.Novanta.Opus532.instrument import QOpus532


class QOpus532Tree(QInstrumentTree):
    '''Parameter tree for a Novanta Opus532 laser.'''

    INSTRUMENT = QOpus532


if __name__ == '__main__':
    QOpus532Tree.example()

__all__ = ['QOpus532Tree']
