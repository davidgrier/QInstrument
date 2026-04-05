from QInstrument.lib.QFakeInstrument import QFakeInstrument
from QInstrument.instruments.IPGLaser.instrument import QIPGLaser


class QFakeIPGLaser(QFakeInstrument, QIPGLaser):
    '''Fake IPG laser for UI development without hardware.

    IPGLaser properties do not use the ``_register()`` helper pattern —
    they derive from a hardware status word via bespoke getters — so this
    fake registers each property explicitly with ``_store``-backed getters
    rather than relying on MRO auto-mock interception.
    '''

    def status(self) -> dict[str, bool | float]:
        '''Return all status properties from the in-memory store.

        Overrides the real ``status()`` to avoid calling ``_flags()``
        and ``_getPower()``, which would attempt serial communication.
        '''
        return {
            'current_setpoint': self._store.get('current_setpoint', 0.),
            'keyswitch':        self._store.get('keyswitch', True),
            'aiming':           self._store.get('aiming', False),
            'emission':         self._store.get('emission', False),
            'fault':            self._store.get('fault', False),
            'power':            self._store.get('power', 0.),
        }

    def _registerProperties(self) -> None:
        self.registerProperty(
            'current_setpoint', ptype=float,
            getter=lambda: self._store.get('current_setpoint', 0.),
            setter=lambda v: self._store.__setitem__(
                'current_setpoint',
                min(float(v),
                    self._store.get('maximum_current', 25.))),
            minimum=0., maximum=100.,
            debounce=500)
        self.registerProperty(
            'maximum_current', ptype=float,
            getter=lambda: self._store.get('maximum_current', 25.),
            setter=lambda v: self._store.__setitem__(
                'maximum_current', max(0., min(float(v), 100.))),
            minimum=0., maximum=100.)
        self.registerProperty(
            'minimum_current', ptype=float, setter=None,
            getter=lambda: self._store.get('minimum_current', 10.))
        self.registerProperty('keyswitch', ptype=bool, setter=None,
                              getter=lambda: self._store.get('keyswitch', True))
        self.registerProperty('aiming', ptype=bool,
                              getter=lambda: self._store.get('aiming', False),
                              setter=lambda v: self._store.__setitem__(
                                  'aiming', bool(v)))
        self.registerProperty('emission', ptype=bool,
                              getter=lambda: self._store.get('emission', False),
                              setter=lambda v: self._store.__setitem__(
                                  'emission', bool(v)))
        self.registerProperty('power', ptype=float, setter=None,
                              getter=lambda: self._store.get('power', 0.))
        self.registerProperty('fault', ptype=bool, setter=None,
                              getter=lambda: self._store.get('fault', False))
        self.identification = 'Fake IPG Fiber Laser'


__all__ = ['QFakeIPGLaser']
