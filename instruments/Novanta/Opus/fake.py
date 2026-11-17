from QInstrument.lib.QFakeInstrument import QFakeInstrument
from QInstrument.instruments.Novanta.Opus.instrument import QOpus


class QFakeOpus(QFakeInstrument, QOpus):
    '''Fake Opus laser for UI development without hardware.

    The Opus property getters call hardware query helpers
    (``_getPower``, ``_getCurrent``, ``_parseTemp``) rather than using
    the ``_register()`` convention, so all properties are registered
    explicitly with ``_store``-backed getters.

    Power clamping mirrors the real instrument: the setter enforces
    ``[MINIMUM_POWER, maximum_power]`` using class attributes resolved
    through the MRO, so thin subclasses (e.g. ``QFakeOpus1064``) inherit
    the correct limits automatically.
    '''

    def _registerProperties(self) -> None:
        register = self.registerProperty
        register('power', ptype=float,
                 getter=lambda: self._store.get('power', 0.),
                 setter=self._fakeSetPower,
                 minimum=self.MINIMUM_POWER,
                 maximum=self.MAXIMUM_POWER)
        register('maximum_power', ptype=float,
                 getter=lambda: self._store.get(
                     'maximum_power', self.MAXIMUM_POWER),
                 setter=lambda v: self._store.__setitem__(
                     'maximum_power',
                     min(max(float(v), self.MINIMUM_POWER),
                         self.MAXIMUM_POWER)),
                 minimum=self.MINIMUM_POWER,
                 maximum=self.MAXIMUM_POWER)
        register('wavelength', ptype=float, setter=None,
                 getter=lambda: self.WAVELENGTH)
        register('minimum_power', ptype=float, setter=None,
                 getter=lambda: self.MINIMUM_POWER)
        register('current', ptype=float,
                 getter=lambda: self._store.get('current', 0.),
                 setter=lambda v: self._store.__setitem__(
                     'current', float(v)))
        register('emission', ptype=bool,
                 getter=lambda: self._store.get('emission', False),
                 setter=lambda v: self._store.__setitem__(
                     'emission', bool(v)))
        register('status', ptype=bool, setter=None,
                 getter=lambda: self._store.get('status', True))
        register('version', ptype=str, setter=None,
                 getter=lambda: self._store.get('version', 'FAKE'))
        register('laser_temperature', ptype=float, setter=None,
                 getter=lambda: self._store.get('laser_temperature', 25.))
        register('psu_temperature', ptype=float, setter=None,
                 getter=lambda: self._store.get('psu_temperature', 25.))
        self.identification = 'Fake Novanta Opus Laser'

    def _fakeSetPower(self, v: float) -> None:
        '''Store power clamped to ``[MINIMUM_POWER, maximum_power]``.

        Parameters
        ----------
        v : float
            Requested output power [mW].
        '''
        max_p = self._store.get('maximum_power', self.MAXIMUM_POWER)
        clamped = min(max(float(v), self.MINIMUM_POWER), max_p)
        self._store['power'] = clamped

    def identify(self) -> bool:
        '''Return True: a fake instrument is always the right device.'''
        return True


__all__ = ['QFakeOpus']
