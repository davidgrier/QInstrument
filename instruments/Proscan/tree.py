from QInstrument.lib.QInstrumentTree import QInstrumentTree
from QInstrument.instruments.Proscan.instrument import QProscan


class QProscanTree(QInstrumentTree):
    '''Parameter tree for the Prior Scientific Proscan stage controller.'''

    INSTRUMENT = QProscan


if __name__ == '__main__':
    QProscanTree.example()

__all__ = ['QProscanTree']
