from __future__ import annotations

from qtpy import QtCore
from QInstrument.lib.QFakeInstrument import QFakeInstrument
from QInstrument.instruments.PriorScientific.Proscan.instrument import QProscan


class QFakeProscan(QFakeInstrument, QProscan):
    '''Simulated Prior Proscan controller for UI development.

    Mirrors all properties of :class:`QProscan` using an in-memory
    store. No hardware is required.
    '''

    positionChanged = QtCore.Signal(object)
    limitsChanged = QtCore.Signal(object)

    def _registerProperties(self) -> None:
        for name, default in (('speed',         50),
                              ('acceleration',  50),
                              ('scurve',        50),
                              ('zspeed',        50),
                              ('zacceleration', 50),
                              ('zscurve',       50)):
            self.registerProperty(
                name,
                getter=lambda n=name, d=default: self._store.get(n, d),
                setter=lambda v, n=name: self._store.update({n: int(v)}),
                ptype=int)
        for name, default in (('stepsize',   1.0),
                              ('zstepsize',  1.0)):
            self.registerProperty(
                name,
                getter=lambda n=name, d=default: self._store.get(n, d),
                setter=lambda v, n=name: self._store.update({n: float(v)}),
                ptype=float)
        for name, default in (('xresolution', 0.1),
                              ('yresolution', 0.1),
                              ('zresolution', 0.1)):
            self.registerProperty(
                name,
                getter=lambda n=name, d=default: self._store.get(n, d),
                setter=None,
                ptype=float)
        for name, default in (('upr',  1.0),
                              ('zupr', 1.0)):
            self.registerProperty(
                name,
                getter=lambda n=name, d=default: self._store.get(n, d),
                setter=lambda v, n=name: self._store.update({n: float(v)}),
                ptype=float)
        self.registerProperty(
            'flip',
            getter=lambda: self._store.get('flip', False),
            setter=lambda v: self._store.update({'flip': bool(v)}),
            ptype=bool)
        self.registerProperty(
            'mirror',
            getter=lambda: self._store.get('mirror', False),
            setter=lambda v: self._store.update({'mirror': bool(v)}),
            ptype=bool)
        self.registerProperty(
            'moving',
            getter=lambda: self._store.get('moving', False),
            setter=None,
            ptype=bool)
        self.registerProperty(
            'limits',
            getter=lambda: self.active_limits(),
            setter=None,
            ptype=object)
        self.identification = 'Fake Prior Proscan'

    def identify(self) -> bool:
        return True

    def position(self) -> list[int]:
        '''Return the simulated stage position and emit positionChanged.'''
        pos = self._store.get('position', [0, 0, 0])
        self.positionChanged.emit(pos)
        return pos

    def set_position(self, position: list[int]) -> bool:
        '''Store the given coordinates as the current simulated position.'''
        self._store['position'] = list(position)
        return True

    def set_origin(self) -> bool:
        '''Set the simulated origin to [0, 0, 0].'''
        self._store['position'] = [0, 0, 0]
        return True

    def status(self) -> int:
        '''Return 0 (not moving, no faults).'''
        return 0

    def emergency_stop(self) -> bool:
        return True

    def triggered_limits(self) -> None:
        return None

    def active_limits(self) -> None:
        return None

    def stop(self) -> bool:
        return True

    def move_to(self, position: list[int],
                relative: bool = False) -> bool:
        if relative:
            current = self._store.get('position', [0, 0, 0])
            position = [c + d for c, d in zip(current, list(position) + [0])]
        self._store['position'] = list(position) + [0] * (3 - len(position))
        return True

    def move_to_origin(self) -> bool:
        self._store['position'] = [0, 0, 0]
        return True

    def set_velocity(self, velocity: list[float]) -> None:
        pass

    def stepLeft(self) -> bool:
        return True

    def stepRight(self) -> bool:
        return True

    def stepForward(self) -> bool:
        return True

    def stepBackward(self) -> bool:
        return True

    def stepUp(self) -> bool:
        return True

    def stepDown(self) -> bool:
        return True

    def description(self) -> list[str]:
        return ['Fake Prior Proscan', 'END']

    def stage(self) -> list[str]:
        return ['Fake XY Stage', 'END']

    def focus(self) -> list[str]:
        return ['Fake Focus Drive', 'END']


__all__ = ['QFakeProscan']
