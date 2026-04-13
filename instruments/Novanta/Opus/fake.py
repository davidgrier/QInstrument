from QInstrument.lib.QFakeInstrument import QFakeInstrument
from QInstrument.instruments.Novanta.Opus.instrument import QOpus


class QFakeOpus(QFakeInstrument, QOpus):
    '''Fake Opus laser for UI development without hardware.

    The Opus property getters call hardware query helpers
    (``_getPower``, ``_getCurrent``, ``_parseTemp``) rather than using
    the ``_register()`` convention, so all properties are registered
    explicitly with ``_store``-backed getters.
    '''

    def _registerProperties(self) -> None:
        default_max = getattr(type(self), 'MAXIMUM_POWER', 1000.)
        self._store.setdefault('maximum_power', default_max)
        self.registerProperty(
            'power', ptype=float,
            getter=lambda: self._store.get('power', 0.),
            setter=lambda v: self._store.__setitem__(
                'power',
                min(float(v), self._store.get('maximum_power', default_max))))
        self.registerProperty(
            'maximum_power', ptype=float,
            getter=lambda: self._store.get('maximum_power', default_max),
            setter=lambda v: self._store.__setitem__('maximum_power', float(v)),
            minimum=0.)
        self.registerProperty(
            'wavelength', ptype=float,
            getter=lambda: self._store.get('wavelength', 532.),
            setter=lambda v: self._store.__setitem__('wavelength', float(v)))
        self.registerProperty(
            'current', ptype=float,
            getter=lambda: self._store.get('current', 0.),
            setter=lambda v: self._store.__setitem__('current', float(v)))
        self.registerProperty(
            'emission', ptype=bool,
            getter=lambda: self._store.get('emission', False),
            setter=lambda v: self._store.__setitem__('emission', bool(v)))
        self.registerProperty(
            'laser_temperature', ptype=float, setter=None,
            getter=lambda: self._store.get('laser_temperature', 25.))
        self.registerProperty(
            'psu_temperature', ptype=float, setter=None,
            getter=lambda: self._store.get('psu_temperature', 25.))
        self.identification = 'Fake Laser Quantum Opus Laser'

    def identify(self) -> bool:
        return True


__all__ = ['QFakeOpus']
