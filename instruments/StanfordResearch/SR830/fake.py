import numpy as np
from QInstrument.lib.QFakeInstrument import QFakeInstrument
from QInstrument.instruments.StanfordResearch.SR830.instrument import QSR830


class QFakeSR830(QFakeInstrument, QSR830):
    '''Fake SR830 for UI development without hardware.

    All read/write properties are backed by an in-memory store via the
    MRO auto-mock pattern.
    '''

    def _registerProperties(self) -> None:
        QSR830._registerProperties(self)
        self.identification = 'Fake SR830 Lock-in Amplifier'

    def identify(self) -> bool:
        return True

    def report(self) -> list[float]:
        '''Return simulated [frequency, R, theta].'''
        data = np.random.rand(3)
        data[2] *= 360.
        return data.tolist()


__all__ = ['QFakeSR830']
