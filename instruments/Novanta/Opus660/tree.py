from QInstrument.lib.QInstrumentTree import QInstrumentTree
from QInstrument.instruments.Novanta.Opus660.instrument import QOpus660


class QOpus660Tree(QInstrumentTree):
    '''Parameter tree for a Novanta Opus660 laser.'''

    INSTRUMENT = QOpus660


if __name__ == '__main__':
    QOpus660Tree.example()

__all__ = ['QOpus660Tree']
