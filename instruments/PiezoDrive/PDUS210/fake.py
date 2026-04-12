from __future__ import annotations

from QInstrument.lib.QFakeInstrument import QFakeInstrument
from QInstrument.instruments.PiezoDrive.PDUS210.instrument import QPDUS210


class QFakePDUS210(QFakeInstrument, QPDUS210):
    '''Simulated PiezoDrive PDUS210 amplifier for UI development.

    Mirrors all properties of :class:`QPDUS210` using an in-memory store.
    No hardware is required.
    '''

    def _registerProperties(self) -> None:
        for name, default in (
                ('frequency',     40000.0),
                ('targetVoltage', 0),
                ('maxFrequency',  45000),
                ('minFrequency',  35000),
                ('targetPhase',   0),
                ('maxLoadPower',  0),
                ('targetPower',   0),
                ('targetCurrent', 0)):
            dtype = float if name == 'frequency' else int
            self.registerProperty(
                name,
                getter=lambda n=name, d=default: self._store.get(n, d),
                setter=lambda v, n=name, t=dtype: self._store.update({n: t(v)}),
                ptype=dtype)
        for name, default in (
                ('phaseGain',   1),
                ('powerGain',   1),
                ('currentGain', 1)):
            self.registerProperty(
                name,
                getter=lambda n=name, d=default: self._store.get(n, d),
                setter=lambda v, n=name: self._store.update({n: int(v)}),
                ptype=int)
        for name in ('phaseTracking', 'powerTracking', 'currentTracking',
                     'frequencyWrapping', 'enabled'):
            self.registerProperty(
                name,
                getter=lambda n=name: self._store.get(n, False),
                setter=lambda v, n=name: self._store.update({n: bool(v)}),
                ptype=bool)
        for name, default, dtype in (
                ('phase',          0,   int),
                ('impedance',      0,   int),
                ('loadPower',      0,   int),
                ('amplifierPower', 0,   int),
                ('current',        0,   int),
                ('temperature',    25.0, float)):
            self.registerProperty(
                name,
                getter=lambda n=name, d=default: self._store.get(n, d),
                setter=None,
                ptype=dtype)

    def identify(self) -> bool:
        return True

    def save(self) -> str:
        return 'OK'

    def state(self) -> dict:
        '''Return a default state dict with all values at their defaults.'''
        return {
            'enabled':          self._store.get('enabled', False),
            'phaseTracking':    self._store.get('phaseTracking', False),
            'currentTracking':  self._store.get('currentTracking', False),
            'powerTracking':    self._store.get('powerTracking', False),
            'errorAmp':         False,
            'errorLoad':        False,
            'errorTemperature': False,
            'voltage':          0.0,
            'frequency':        self._store.get('frequency', 40000.0),
            'minFrequency':     float(self._store.get('minFrequency', 35000)),
            'maxFrequency':     float(self._store.get('maxFrequency', 45000)),
            'targetPhase':      float(self._store.get('targetPhase', 0)),
            'phaseControlGain': float(self._store.get('phaseGain', 1)),
            'maxLoadPower':     float(self._store.get('maxLoadPower', 0)),
            'amplifierPower':   float(self._store.get('amplifierPower', 0)),
            'loadPower':        float(self._store.get('loadPower', 0)),
            'temperature':      self._store.get('temperature', 25.0),
            'measuredPhase':    float(self._store.get('phase', 0)),
            'measuredCurrent':  float(self._store.get('current', 0)),
            'impedance':        float(self._store.get('impedance', 0)),
            'transformerTurns': 1.0,
        }


__all__ = ['QFakePDUS210']
