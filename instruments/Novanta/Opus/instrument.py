import logging
from QInstrument.lib.QSerialInstrument import QSerialInstrument


logger = logging.getLogger(__name__)


class QOpus(QSerialInstrument):
    '''Laser Quantum Opus Continuous-wave Laser

    The Opus command interface uses plain text:
    - Queries end in ``?`` and return a value with a units suffix
      (e.g. ``POWER?`` → ``'0123.4mW'``).
    - Setpoint commands use ``CMD=value`` syntax
      (e.g. ``POWER=100.0``).
    - Boolean commands are sent as plain mnemonics (``ON``, ``OFF``).

    Properties
    ==========

    Control
    -------
    power : float [mW]
        Getter returns the actual output power.
        Setter transmits a new power setpoint, clamped to ``maximum_power``.
    maximum_power : float [mW]
        Software upper bound on the power setpoint.  Default: 1000.
        Not discoverable from the hardware; set at startup and persisted
        via the saved configuration.
    wavelength : float [nm]
        Emission wavelength of the specific laser unit.  Default: 532.
        Not discoverable from the hardware; set at startup and persisted
        via the saved configuration.
    current : float [%]
        Diode current as a percentage of maximum.
    emission : bool
        True: laser emission enabled. False: emission disabled.

    Status (read-only)
    ------------------
    laser_temperature : float [°C]
        Laser head temperature.
    psu_temperature : float [°C]
        Power supply unit temperature.
    '''

    comm = dict(baudRate=QSerialInstrument.BaudRate.Baud19200,
                dataBits=QSerialInstrument.DataBits.Data8,
                stopBits=QSerialInstrument.StopBits.OneStop,
                parity=QSerialInstrument.Parity.NoParity,
                flowControl=QSerialInstrument.FlowControl.NoFlowControl,
                eol='\r\n',
                timeout=500)

    def _registerProperties(self) -> None:
        '''Register all instrument properties via ``registerProperty()``.

        Called once from ``__init__``. Subclasses that extend the property
        set should call ``super()._registerProperties()`` first.

        ``maximum_power`` and ``wavelength`` are not discoverable from the
        hardware at runtime.  They are initialised to defaults here and
        restored from the saved configuration on the first widget show.
        '''
        self._maximum_power = 1000.
        self._wavelength = 532.
        self._power: float = 0.
        register = self.registerProperty
        register('power', ptype=float,
                 getter=self._getPower,
                 setter=self._setPower)
        register('maximum_power', ptype=float,
                 getter=lambda: self._maximum_power,
                 setter=self._setMaximumPower,
                 minimum=0.)
        register('wavelength', ptype=float,
                 getter=lambda: self._wavelength,
                 setter=lambda v: setattr(self, '_wavelength', float(v)))
        register('current', ptype=float,
                 getter=self._getCurrent,
                 setter=lambda v: self.transmit(f'CURRENT={float(v)}'))
        register('emission', ptype=bool,
                 getter=lambda: self._power > 0,
                 setter=self._setEmission)
        register('version', ptype=str, setter=None, getter=self.version)
        register('laser_temperature', ptype=float, setter=None,
                 getter=lambda: self._parseTemp('LASTEMP?'))
        register('psu_temperature', ptype=float, setter=None,
                 getter=lambda: self._parseTemp('PSUTEMP?'))

    def identify(self) -> bool:
        '''Return True if the connected device identifies as an Opus laser.

        Queries the firmware version and checks for the
        ``'MPC-D'`` controller model token in the response.
        '''
        return 'MPC-D' in self.version()

    def _getPower(self) -> float:
        '''Query and return the actual output power [mW].

        The instrument responds with a value and ``mW`` suffix
        (e.g. ``'0123.4mW'``).  Caches the result in ``_power`` so
        the ``emission`` getter can read it without a second query.
        '''
        response = self.handshake('POWER?')
        if response:
            self._power = float(response.rstrip('mW'))
        return self._power

    def _getCurrent(self) -> float:
        '''Query and return the diode current [%].

        The instrument responds with a value and ``%`` suffix
        (e.g. ``'050.0%'``).
        '''
        response = self.handshake('CURRENT?')
        return float(response.rstrip('%')) if response else 0.

    def _parseTemp(self, cmd: str) -> float:
        '''Query a temperature command and return the value [°C].

        Strips trailing unit characters (``C``) before conversion.

        Parameters
        ----------
        cmd : str
            Temperature query mnemonic (``'LASTEMP?'`` or ``'PSUTEMP?'``).
        '''
        response = self.handshake(cmd)
        return float(response.rstrip(' C')) if response else 0.

    def _setPower(self, v: float) -> None:
        '''Transmit a new power setpoint, clamped to ``maximum_power``.

        Parameters
        ----------
        v : float
            Requested output power [mW].
        '''
        limit = self._maximum_power
        clamped = min(float(v), limit)
        if clamped < float(v):
            logger.warning(
                f'power {v:.1f} mW exceeds maximum_power '
                f'{limit:.1f} mW; clamped to {clamped:.1f} mW')
        self.transmit(f'POWER={clamped}')

    def _setMaximumPower(self, v: float) -> None:
        '''Set the software upper bound on the power setpoint.

        Values at or below zero are rejected and a warning is logged.

        Parameters
        ----------
        v : float
            New maximum output power [mW].
        '''
        v = float(v)
        if v <= 0.:
            logger.warning(
                f'maximum_power {v:.1f} mW must be positive; ignored')
            return
        self._maximum_power = v

    def _setEmission(self, state: bool) -> None:
        '''Enable or disable laser emission.

        Parameters
        ----------
        state : bool
            True to enable (``ON``), False to disable (``OFF``).
        '''
        self.transmit('ON' if bool(state) else 'OFF')

    def version(self) -> str:
        '''Return the firmware version string.'''
        return self.handshake('VERSION?')

    def timers(self) -> list[str]:
        '''Return laser and PSU on-time readings.

        Sends ``TIMERS?`` and collects response lines until a line not
        containing ``'Hours'`` is received.  The terminating line is
        discarded.

        Returns
        -------
        list[str]
            Lines containing timer readings
            (e.g. ``'Laser head: 12345 Hours'``).
        '''
        self.transmit('TIMERS?')
        lines = []
        while True:
            line = self.receive()
            if 'Hours' not in line:
                break
            lines.append(line)
        return lines


if __name__ == '__main__':
    QOpus.example()

__all__ = ['QOpus']
