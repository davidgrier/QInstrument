from __future__ import annotations

import logging
from struct import unpack
from QInstrument.lib.QSerialInstrument import QSerialInstrument

logger = logging.getLogger(__name__)


class QPDUS210(QSerialInstrument):
    '''PiezoDrive PDUS210 Ultrasonic Power Amplifier.

    Controls a PiezoDrive PDUS210 piezoelectric amplifier over RS-232.

    Properties
    ==========

    Setpoints
    ---------
    frequency : float [Hz]
        Output drive frequency.
    targetVoltage : int [V pp]
        Target output voltage, peak-to-peak.
    maxFrequency : int [Hz]
        Maximum allowed drive frequency.
    minFrequency : int [Hz]
        Minimum allowed drive frequency.
    targetPhase : int [degrees]
        Target phase between voltage and current.
    maxLoadPower : int [W]
        Maximum load power limit.
    targetPower : int [W]
        Target drive power.
    targetCurrent : int [mA]
        Target drive current.

    Control Gains
    -------------
    phaseGain : int
        Gain of the phase-tracking control loop.
    powerGain : int
        Gain of the power-tracking control loop.
    currentGain : int
        Gain of the current-tracking control loop.

    Tracking Modes
    --------------
    phaseTracking : bool
        True: enable phase-tracking mode.
    powerTracking : bool
        True: enable power-tracking mode.
    currentTracking : bool
        True: enable current-tracking mode.
    frequencyWrapping : bool
        True: enable frequency wrapping at the frequency limits.
    enabled : bool
        True: enable the amplifier output.

    Measurements (read-only)
    ------------------------
    phase : int [degrees]
        Measured phase between voltage and current.
    impedance : int [Ω]
        Measured load impedance.
    loadPower : int [W]
        Measured load power.
    amplifierPower : int [W]
        Measured total amplifier power.
    current : int [mA]
        Measured drive current.
    temperature : float [°C]
        Measured amplifier temperature.
    '''

    comm = dict(baudRate=QSerialInstrument.BaudRate.Baud9600,
                dataBits=QSerialInstrument.DataBits.Data8,
                stopBits=QSerialInstrument.StopBits.OneStop,
                parity=QSerialInstrument.Parity.NoParity,
                flowControl=QSerialInstrument.FlowControl.NoFlowControl,
                timeout=1000,
                eol='\r')

    def _registerProperties(self) -> None:
        for name, cmd, dtype in (
                ('frequency',     'FREQ',    float),
                ('targetVoltage', 'VOLT',    int),
                ('maxFrequency',  'MAXFREQ', int),
                ('minFrequency',  'MINFREQ', int),
                ('targetPhase',   'PHASE',   int),
                ('maxLoadPower',  'MAXLPOW', int),
                ('targetPower',   'TARPOW',  int),
                ('targetCurrent', 'CURRENT', int)):
            self.registerProperty(
                name,
                getter=lambda c=cmd, t=dtype: self.getValue(f'get{c}', t),
                setter=lambda v, c=cmd, t=dtype: self.transmit(f'set{c}{t(v)}'),
                ptype=dtype)
        for name, gcmd, scmd in (
                ('phaseGain',   'PHASEGAIN',   'GAINPHASE'),
                ('powerGain',   'POWERGAIN',   'GAINPOWER'),
                ('currentGain', 'CURRENTGAIN', 'GAINCURRENT')):
            self.registerProperty(
                name,
                getter=lambda g=gcmd: self.getValue(f'get{g}', int),
                setter=lambda v, s=scmd: self.transmit(f'set{s}{int(v)}'),
                ptype=int)
        for name, pstr in (
                ('phaseTracking',     'PHASE'),
                ('powerTracking',     'POWER'),
                ('currentTracking',   'CURRENT'),
                ('frequencyWrapping', 'WRAP'),
                ('enabled',           'ENABLE')):
            self.registerProperty(
                name,
                getter=lambda p=pstr: self.getValue(f'is{p}', str) == 'TRUE',
                setter=lambda v, p=pstr: self._toggle(p, bool(v)),
                ptype=bool)
        for name, cmd, dtype in (
                ('phase',          'PHASE',   int),
                ('impedance',      'IMP',     int),
                ('loadPower',      'LPOW',    int),
                ('amplifierPower', 'APOW',    int),
                ('current',        'CURRENT', int),
                ('temperature',    'TEMP',    float)):
            self.registerProperty(
                name,
                getter=lambda c=cmd, t=dtype: self.getValue(f'read{c}', t),
                setter=None,
                ptype=dtype)

    def identify(self) -> bool:
        '''Return True if the controller responds to DISABLE with FALSE.

        Sending DISABLE on identification also places the amplifier in its
        safe disabled state.
        '''
        return 'FALSE' in self.handshake('DISABLE')

    def save(self) -> str:
        '''Save current parameters to permanent storage.

        Returns
        -------
        str
            The controller acknowledgment string.
        '''
        return self.handshake('SAVE')

    def state(self) -> dict:
        '''Read all controller state in one serial command.

        Transmits ``getSTATE`` and reads the 80-byte binary response,
        which encodes 7 boolean flags followed by 18 float measurements.

        Returns
        -------
        dict
            Mapping of state variable names to their current values.
        '''
        self.transmit('getSTATE')
        data = self._interface.readn(80)
        keys = ['enabled', 'phaseTracking', 'currentTracking', 'powerTracking',
                'errorAmp', 'errorLoad', 'errorTemperature',
                'voltage', 'frequency', 'minFrequency', 'maxFrequency',
                'targetPhase', 'phaseControlGain',
                'maxLoadPower', 'amplifierPower', 'loadPower',
                'temperature', 'measuredPhase', 'measuredCurrent',
                'impedance', 'transformerTurns']
        vals = unpack('<7cx18f', data)
        return dict(zip(keys, vals))

    def _toggle(self, pstr: str, enable: bool) -> None:
        if pstr == 'ENABLE':
            cmd = 'ENABLE' if enable else 'DISABLE'
        else:
            cmd = f'en{pstr}' if enable else f'dis{pstr}'
        self.transmit(cmd)


__all__ = ['QPDUS210']


if __name__ == '__main__':
    QPDUS210.example()
