from QInstrument.lib.QInstrumentTree import QInstrumentTree
from QInstrument.instruments.IPGLaser.instrument import QIPGLaser


class QIPGLaserTree(QInstrumentTree):
    '''Parameter tree for an IPG fiber laser.'''

    INSTRUMENT = QIPGLaser


if __name__ == '__main__':
    QIPGLaserTree.example()

__all__ = ['QIPGLaserTree']
