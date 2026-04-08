from QInstrument.lib.QInstrumentTree import QInstrumentTree
from QInstrument.instruments.Opus.instrument import QOpus


class QOpusTree(QInstrumentTree):
    '''Parameter tree for a Laser Quantum Opus laser.'''

    INSTRUMENT = QOpus


if __name__ == '__main__':
    QOpusTree.example()

__all__ = ['QOpusTree']
