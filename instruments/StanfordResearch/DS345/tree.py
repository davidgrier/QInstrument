from QInstrument.lib.QInstrumentTree import QInstrumentTree
from QInstrument.instruments.StanfordResearch.DS345.instrument import QDS345


class QDS345Tree(QInstrumentTree):
    '''Parameter tree for the Stanford Research Systems DS345 Function Generator.'''

    INSTRUMENT = QDS345


if __name__ == '__main__':
    QDS345Tree.example()

__all__ = ['QDS345Tree']
