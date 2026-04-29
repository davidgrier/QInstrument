import numpy as np
from QInstrument.lib.QFakeInstrument import QFakeInstrument
from QInstrument.instruments.StanfordResearch.SR844.instrument import QSR844


class QFakeSR844(QFakeInstrument, QSR844):
    '''Fake SR844 for UI development without hardware.

    All read/write properties are backed by an in-memory store via the
    MRO auto-mock pattern.
    '''

    def _registerProperties(self) -> None:
        QSR844._registerProperties(self)
        self.identification = 'Fake SR844 RF Lock-in Amplifier'

    def identify(self) -> bool:
        return True

    def report(self) -> list[float]:
        '''Return simulated [frequency, R, theta].'''
        data = np.random.rand(3)
        data[2] *= 360.
        return data.tolist()


__all__ = ['QFakeSR844']
