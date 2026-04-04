from QInstrument.lib.QFakeInstrument import QFakeInstrument
from QInstrument.instruments.DS345.instrument import QDS345


class QFakeDS345(QFakeInstrument, QDS345):
    '''Fake DS345 for UI development without hardware.

    All standard properties are backed by an in-memory store via
    ``QFakeInstrument._register()``.  ``amplitude`` uses a non-standard
    DS345 response format (``'1.000VP'``) so its getter and setter are
    re-registered here after the parent registration runs.
    '''

    def _registerProperties(self) -> None:
        QDS345._registerProperties(self)
        self.registerProperty('amplitude',
                              getter=lambda: self._store.get('amplitude', 1.),
                              setter=lambda v: self._store.__setitem__('amplitude', float(v)))


__all__ = ['QFakeDS345']
