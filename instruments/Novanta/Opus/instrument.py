import logging
from QInstrument.lib.QSerialInstrument import QSerialInstrument


logger = logging.getLogger(__name__)


class QOpus(QSerialInstrument):
    '''Novanta Opus continuous-wave laser.

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
        Setter transmits a new power setpoint, clamped to
        ``[MINIMUM_POWER, maximum_power]``.
    maximum_power : float [mW]
        Software upper bound on the power setpoint.  Initialised from
        :attr:`MAXIMUM_POWER` and persisted via the saved configuration.
        Accepts values in ``[MINIMUM_POWER, MAXIMUM_POWER]``.
    current : float [%]
        Diode current as a percentage of maximum.
    emission : bool
        True: laser emission enabled. False: emission disabled.

    Status (read-only)
    ------------------
    status : bool
        True if the laser is ENABLED (interlock satisfied and ready to
        emit).  False if DISABLED (keyswitch off or enable button not
        pressed); a warning is logged when DISABLED is received.
    wavelength : float [nm]
        Emission wavelength.  Fixed at :attr:`WAVELENGTH`.
    minimum_power : float [mW]
        Hardware minimum power setpoint.  Fixed at :attr:`MINIMUM_POWER`.
    laser_temperature : float [°C]
        Laser head temperature.
    psu_temperature : float [°C]
        Power supply unit temperature.

    Class Attributes
    ----------------
    WAVELENGTH : float
        Emission wavelength [nm].  Set by each model subclass.
    MINIMUM_POWER : float
        Hardware minimum output power [mW].  0 for most models;
        2000 for the Opus1064.
    MAXIMUM_POWER : float
        Hardware maximum output power [mW].  Used to initialise the
        ``maximum_power`` soft cap and as the upper bound for the
        ``power`` property metadata.
    '''

    WAVELENGTH: float = 0.       # nm — subclasses override
    MINIMUM_POWER: float = 0.    # mW
    MAXIMUM_POWER: float = 1000. # mW — conservative default; subclasses override

    comm = dict(baudRate=QSerialInstrument.BaudRate.Baud19200,
                dataBits=QSerialInstrument.DataBits.Data8,
                stopBits=QSerialInstrument.StopBits.OneStop,
                parity=QSerialInstrument.Parity.NoParity,
                flowControl=QSerialInstrument.FlowControl.NoFlowControl,
                eol='\r\n',
                timeout=500)

    def _registerProperties(self) -> None:
        '''Register all instrument properties via ``registerProperty()``.

        Called once from ``__init__``.  Subclasses that extend the
        property set should call ``super()._registerProperties()`` first.

        ``maximum_power`` is initialised from :attr:`MAXIMUM_POWER` and
        restored from saved configuration on the first widget show.
        ``wavelength`` and ``minimum_power`` are read-only constants
        derived from class attributes.
        '''
        self._maximum_power: float = self.MAXIMUM_POWER
        self._power: float = 0.
        register = self.registerProperty
        register('power', ptype=float,
                 getter=self._getPower,
                 setter=self._setPower,
                 minimum=self.MINIMUM_POWER,
                 maximum=self.MAXIMUM_POWER)
        register('maximum_power', ptype=float,
                 getter=lambda: self._maximum_power,
                 setter=self._setMaximumPower,
                 minimum=self.MINIMUM_POWER,
                 maximum=self.MAXIMUM_POWER)
        register('wavelength', ptype=float, setter=None,
                 getter=lambda: self.WAVELENGTH)
        register('minimum_power', ptype=float, setter=None,
                 getter=lambda: self.MINIMUM_POWER)
        register('current', ptype=float,
                 getter=self._getCurrent,
                 setter=lambda v: self.handshake(f'CURRENT={float(v)}'))
        register('emission', ptype=bool,
                 getter=lambda: self._power > 0,
                 setter=self._setEmission)
        register('status', ptype=bool, setter=None,
                 getter=self._getStatus)
        register('version', ptype=str, setter=None, getter=self.version)
        register('laser_temperature', ptype=float, setter=None,
                 getter=lambda: self._parseTemp('LASTEMP?'))
        register('psu_temperature', ptype=float, setter=None,
                 getter=lambda: self._parseTemp('PSUTEMP?'))

    def identify(self) -> bool:
        '''Return True if the connected device identifies as an Opus laser.

        Queries the firmware version and checks for the ``'MPC-D'``
        controller model token in the response.  On success, sends
        ``CONTROL=POWER`` to ensure the controller regulates output
        power rather than diode current for all subsequent setpoint
        commands.
        '''
        if 'MPC-D' not in self.version():
            return False
        self.handshake('CONTROL=POWER')
        return True

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

    def _getStatus(self) -> bool:
        '''Query and return the laser enable status.

        Returns
        -------
        bool
            True if the laser responds ``ENABLED``.
            False if the laser responds ``DISABLED``; a warning is
            logged in that case because the condition requires user
            intervention (keyswitch or enable button).
        '''
        response = self.handshake('STATUS?')
        if response == 'DISABLED':
            logger.warning(
                'Opus laser is DISABLED: '
                'check keyswitch and front-panel enable button')
            return False
        return response == 'ENABLED'

    def _setPower(self, v: float) -> None:
        '''Transmit a new power setpoint, clamped to ``[MINIMUM_POWER,
        maximum_power]``.

        Parameters
        ----------
        v : float
            Requested output power [mW].
        '''
        v = float(v)
        clamped = min(max(v, self.MINIMUM_POWER), self._maximum_power)
        if clamped != v:
            logger.warning(
                f'power {v:.1f} mW out of range '
                f'[{self.MINIMUM_POWER:.1f}, {self._maximum_power:.1f}] mW; '
                f'clamped to {clamped:.1f} mW')
        self.handshake(f'POWER={clamped}')

    def _setMaximumPower(self, v: float) -> None:
        '''Set the software upper bound on the power setpoint.

        Rejects non-positive values and values outside
        ``[MINIMUM_POWER, MAXIMUM_POWER]``, and
        logs a warning.

        Parameters
        ----------
        v : float
            New maximum output power [mW].
        '''
        v = float(v)
        if v <= 0. or v < self.MINIMUM_POWER or v > self.MAXIMUM_POWER:
            logger.warning(
                f'maximum_power {v:.1f} mW out of range '
                f'[{self.MINIMUM_POWER:.1f}, {self.MAXIMUM_POWER:.1f}] mW; '
                'ignored')
            return
        self._maximum_power = v

    def _setEmission(self, state: bool) -> None:
        '''Enable or disable laser emission.

        Parameters
        ----------
        state : bool
            True to enable (``ON``), False to disable (``OFF``).
        '''
        self.handshake('ON' if bool(state) else 'OFF')

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
