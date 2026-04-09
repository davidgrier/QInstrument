from QInstrument.lib.QInstrumentTree import QInstrumentTree
from QInstrument.instruments.PiezoDrive.instrument import QPDUS210


class QPDUS210Tree(QInstrumentTree):
    '''Parameter tree for the PiezoDrive PDUS210 ultrasonic amplifier.'''

    INSTRUMENT = QPDUS210


if __name__ == '__main__':
    QPDUS210Tree.example()

__all__ = ['QPDUS210Tree']
