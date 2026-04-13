import numpy as np
from QInstrument.lib.QFakeInstrument import QFakeInstrument
from QInstrument.instruments.StanfordResearch.SR830.instrument import QSR830


class QFakeSR830(QFakeInstrument, QSR830):
    '''Fake SR830 for UI development without hardware.

    All standard read/write properties are backed by an in-memory store
    via the MRO auto-mock pattern.  The four read-only output channels
    (x, y, r, theta) are re-registered here to return ``0.0`` from the
    store rather than attempting wire communication.
    '''

    def _registerProperties(self) -> None:
        QSR830._registerProperties(self)
        for name in ('x', 'y', 'r', 'theta'):
            self.registerProperty(name, setter=None, ptype=float,
                                  getter=lambda n=name: self._store.get(n, 0.))
        self.identification = 'Fake SR830 Lock-in Amplifier'

    def identify(self) -> bool:
        return True

    def report(self) -> list[float]:
        '''Return simulated [frequency, R, theta].'''
        data = np.random.rand(3)
        data[2] *= 360.
        return data.tolist()


__all__ = ['QFakeSR830']
