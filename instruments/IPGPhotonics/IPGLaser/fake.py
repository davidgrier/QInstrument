from QInstrument.lib.QFakeInstrument import QFakeInstrument
from QInstrument.instruments.IPGPhotonics.IPGLaser.instrument import QIPGLaser


class QFakeIPGLaser(QFakeInstrument, QIPGLaser):
    '''Fake IPG laser for UI development without hardware.

    IPGLaser properties do not use the ``_register()`` helper pattern —
    they derive from a hardware status word via bespoke getters — so this
    fake registers each property explicitly with ``_store``-backed getters
    rather than relying on MRO auto-mock interception.
    '''

    def status(self) -> dict[str, bool | float]:
        '''Return all polled status properties from the in-memory store.

        Overrides the real ``status()`` to avoid calling ``_flags()``
        and ``_getPower()``, which would attempt serial communication.
        '''
        return {
            'power_supply': self._store.get('power_supply', True),
            'keyswitch':    self._store.get('keyswitch', True),
            'aiming':       self._store.get('aiming', False),
            'emission':     self._store.get('emission', False),
            'fault':        self._store.get('fault', False),
            'power':        self._store.get('power', 0.),
        }

    def _registerProperties(self) -> None:
        self._minimum_current = 10.
        self.registerProperty(
            'current', ptype=float,
            getter=lambda: self._store.get('current', 0.),
            setter=lambda v: self._store.__setitem__(
                'current',
                min(float(v), self._store.get('maximum_current', 100.))),
            minimum=0., maximum=100.,
            debounce=500)
        self.registerProperty(
            'maximum_current', ptype=float,
            getter=lambda: self._store.get('maximum_current', 100.),
            setter=lambda v: self._store.__setitem__(
                'maximum_current', float(v)),
            minimum=0., maximum=100.)
        self.registerProperty(
            'aiming', ptype=bool,
            getter=lambda: self._store.get('aiming', False),
            setter=lambda v: self._store.__setitem__('aiming', bool(v)))
        self.registerProperty(
            'emission', ptype=bool,
            getter=lambda: self._store.get('emission', False),
            setter=lambda v: self._store.__setitem__('emission', bool(v)))
        self.registerProperty(
            'power', ptype=float, setter=None,
            getter=lambda: self._store.get('power', 0.))
        self.registerProperty(
            'power_supply', ptype=bool, setter=None,
            getter=lambda: self._store.get('power_supply', True))
        self.registerProperty(
            'keyswitch', ptype=bool, setter=None,
            getter=lambda: self._store.get('keyswitch', True))
        self.registerProperty(
            'fault', ptype=bool, setter=None,
            getter=lambda: self._store.get('fault', False))
        self.registerProperty(
            'minimum_current', ptype=float, setter=None,
            getter=lambda: self._minimum_current)
        self.registerProperty(
            'firmware', ptype=str, setter=None,
            getter=lambda: self._store.get('firmware', 'Fake IPG v1.0'))
        self.registerProperty(
            'temperature', ptype=float, setter=None,
            getter=lambda: self._store.get('temperature', 25.))
        self.identification = 'Fake IPG Fiber Laser'


__all__ = ['QFakeIPGLaser']
