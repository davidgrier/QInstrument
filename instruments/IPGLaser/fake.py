from QInstrument.lib.QFakeInstrument import QFakeInstrument
from QInstrument.instruments.IPGLaser.instrument import QIPGLaser


class QFakeIPGLaser(QFakeInstrument, QIPGLaser):
    '''Fake IPG laser for UI development without hardware.

    IPGLaser properties do not use the ``_register()`` helper pattern —
    they derive from a hardware status word via bespoke getters — so this
    fake registers each property explicitly with ``_store``-backed getters
    rather than relying on MRO auto-mock interception.
    '''

    def _registerProperties(self) -> None:
        self.registerProperty('keyswitch', ptype=bool, setter=None,
                              getter=lambda: self._store.get('keyswitch', True))
        self.registerProperty('aiming', ptype=bool,
                              getter=lambda: self._store.get('aiming', False),
                              setter=lambda v: self._store.__setitem__('aiming', bool(v)))
        self.registerProperty('emission', ptype=bool,
                              getter=lambda: self._store.get('emission', False),
                              setter=lambda v: self._store.__setitem__('emission', bool(v)))
        self.registerProperty('power', ptype=float, setter=None,
                              getter=lambda: self._store.get('power', 0.))
        self.registerProperty('fault', ptype=bool, setter=None,
                              getter=lambda: self._store.get('fault', False))
        self.identification = 'Fake IPG Fiber Laser'


__all__ = ['QFakeIPGLaser']
