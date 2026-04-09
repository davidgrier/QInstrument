from QInstrument.lib.QFakeInstrument import QFakeInstrument
from QInstrument.instruments.StanfordResearch.DS345.instrument import QDS345


class QFakeDS345(QFakeInstrument, QDS345):
    '''Fake DS345 for UI development without hardware.

    All standard properties are backed by an in-memory store via
    ``QFakeInstrument._register()``.  Two properties are re-registered
    after the parent registration runs:

    - ``amplitude``: the real instrument uses a non-standard response
      format (``'1.000VP'``), so the fake uses a plain float store entry.
    - ``mute``: the real setter calls ``transmit()``, which is a no-op in
      the fake.  The fake setter updates ``_store['amplitude']`` directly
      so that the amplitude widget reflects the muted/unmuted state.
    '''

    def _registerProperties(self) -> None:
        QDS345._registerProperties(self)
        self.registerProperty('amplitude',
                              getter=lambda: self._store.get('amplitude', 1.),
                              setter=lambda v: self._store.__setitem__('amplitude', float(v)))

        def _mute_setter(v: bool) -> None:
            v = bool(v)
            if v == self._muted:
                return
            if v:
                self._saved_amplitude = self._store.get('amplitude', 1.)
                self._store['amplitude'] = 0.
                self._muted = True
            else:
                self._muted = False
                self._store['amplitude'] = self._saved_amplitude

        self.registerProperty('mute', ptype=bool,
                              getter=lambda: self._muted,
                              setter=_mute_setter)


__all__ = ['QFakeDS345']
