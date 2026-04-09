import numpy as np
from QInstrument.lib.QFakeInstrument import QFakeInstrument
from QInstrument.instruments.SR844.instrument import QSR844


class QFakeSR844(QFakeInstrument, QSR844):
    '''Fake SR844 for UI development without hardware.

    All standard read/write properties are backed by an in-memory store
    via the MRO auto-mock pattern.  The read-only output channels
    (x, y, r, theta, reference_frequency, if_frequency) are re-registered
    here to return ``0`` or ``0.0`` from the store rather than attempting
    wire communication.
    '''

    def _registerProperties(self) -> None:
        QSR844._registerProperties(self)
        for name in ('x', 'y', 'r', 'theta'):
            self.registerProperty(name, setter=None, ptype=float,
                                  getter=lambda n=name: self._store.get(n, 0.))
        for name in ('reference_frequency', 'if_frequency'):
            self.registerProperty(name, setter=None, ptype=int,
                                  getter=lambda n=name: self._store.get(n, 0))
        self.identification = 'Fake SR844 RF Lock-in Amplifier'

    def report(self) -> list[float]:
        '''Return simulated [frequency, R, theta].'''
        data = np.random.rand(3)
        data[2] *= 360.
        return data.tolist()


__all__ = ['QFakeSR844']
