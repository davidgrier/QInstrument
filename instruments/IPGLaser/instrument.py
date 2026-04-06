import logging
from QInstrument.lib.QSerialInstrument import QSerialInstrument


logger = logging.getLogger(__name__)


class QIPGLaser(QSerialInstrument):
    '''IPG Photonics YLR Ytterbium Fiber Laser.

    The IPG command interface does not follow the ``CMD?`` / ``CMDvalue``
    convention used by SRS instruments.  Each command is a short mnemonic
    that either queries the instrument (e.g. ``STA``, ``ROP``) or
    commands it (e.g. ``ABN``, ``EMOFF``).  All responses echo the
    command name followed by the value.  Properties are therefore
    registered with bespoke getters and setters rather than a
    ``_register()`` helper.

    Properties
    ==========

    Control
    -------
    current : float [%]
        Diode current setpoint as a percentage of maximum.
        Range: ``minimum_current``--``maximum_current``.  Commands
        ``SDC``; read back via ``RCS``.
    maximum_current : float [%]
        Software upper bound on the current setpoint.
        Range: 0--100.  Default: 100.  Values above this limit are
        clamped and a warning is logged.
    aiming : bool
        True: aiming beam on (``ABN``). False: aiming beam off (``ABF``).
    emission : bool
        True: laser emission enabled (``EMON``).
        False: emission off (``EMOFF``).

    Status (read-only)
    ------------------
    power : float [W]
        Current output power (``ROP``).
    power_supply : bool
        True: power supply is on.
    keyswitch : bool
        True: keyswitch in REM (remote) position.
    fault : bool
        True: one or more fault conditions are active.
        Fault conditions: over-temperature, excessive backreflection,
        power supply off, unexpected emission detected.
    minimum_current : float [%]
        Minimum effective diode current percentage.  Read once at
        startup via ``RNC`` and cached for the session.
    firmware : str
        Firmware version string (``RFV``).
    temperature : float [deg C]
        Laser diode temperature (``RCT``).

    Reference
    =========
    IPG Photonics Fiber Laser User Manual, dated February 26, 2010.

    Interface Commands
    |---------+--------------------------+--------------------------|
    | Command | Description              | Response                 |
    |---------+--------------------------+--------------------------|
    | SDC v   | Set Diode Current        | SDC: v                   |
    |         | v: percent of full range | ERR: Out of range        |
    | RCS     | Read Current Setpoint    | RCS: v                   |
    | RNC     | Read Minimum Current     | RNC: v                   |
    | RDC     | Read Diode Current       | RDC: v                   |
    |         | v: Amps                  |                          |
    | ROP     | Read Output Power        | ROP: v                   |
    |         | v: Watts                 | ROP: Off                 |
    |         |                          | ROP: Low                 |
    | RFV     | Read Firmware Version    | RFV: version             |
    | RCT     | Read Laser Temperature   | RCT: v                   |
    |         | v: degrees Centigrade    |                          |
    | STA     | Read Device Status       | STA: v                   |
    |         | v: int: status bits      |                          |
    | EMON    | Start Emission           | EMON                     |
    |         |                          | ERR: Keyswitch in remote |
    | EMOFF   | Stop Emission            | EMOFF                    |
    |         |                          | ERR: Keyswitch in remote |
    | EMOD    | Enable Modulation        | EMOD                     |
    |         |                          | ERR: Emission is on      |
    | DMOD    | Disable Modulation       | DMOD                     |
    |         |                          | ERR: Emission is on      |
    | EEC     | Enable External Control  | EEC                      |
    |         | analog control           | ERR: Emission is on      |
    | DEC     | Disable External Control | DEC                      |
    |         |                          | ERR: Emission is on      |
    | RERR    | Reset Errors             | RERR                     |
    | ABN     | Aiming Beam On           | ABN                      |
    | ABF     | Aiming Beam Off          | ABF                      |
    | EEABC   | Enable External          | EEABC                    |
    |         | Aiming Beam Control      |                          |
    | DEABC   | Disable EABC             | DEABC                    |
    | SFWS v  | Set Filter Window Size   | SFWS: v                  |
    |         | v: averaging time [s]    | ERR: Out of Range        |
    |         | multiple of 0.2 s        |                          |
    | RFWS    | Read Filter Window Size  | RFWS: v                  |
    |---------+--------------------------+--------------------------|
    '''

    flag = {'TMP': 0x2,        # over-temperature condition
            'EMX': 0x4,        # laser emission active
            'BKR': 0x8,        # excessive backreflection
            'ACL': 0x10,       # analog control mode enabled
            'MDC': 0x40,       # module communication disconnected
            'MFL': 0x80,       # module(s) failed
            'AIM': 0x100,      # aiming beam on
            'PWR': 0x800,      # power supply off
            'MOD': 0x1000,     # modulation enabled
            'ENA': 0x4000,     # laser enable asserted
            'EMS': 0x8000,     # emission startup
            'UNX': 0x20000,    # unexpected emission detected
            'KEY': 0x200000,   # keyswitch in REM position
            'ERR': 0x2 | 0x8 | 0x800 | 0x20000}  # composite fault mask

    comm = dict(baudRate=QSerialInstrument.BaudRate.Baud57600,
                dataBits=QSerialInstrument.DataBits.Data8,
                stopBits=QSerialInstrument.StopBits.OneStop,
                parity=QSerialInstrument.Parity.NoParity,
                flowControl=QSerialInstrument.FlowControl.NoFlowControl,
                eol='\r')

    def _registerProperties(self) -> None:
        '''Register all instrument properties via ``registerProperty()``.

        Called once from ``__init__``.  ``minimum_current`` defaults to
        ``0.`` until ``identify()`` reads the hardware value at open time.
        Subclasses that extend the property set should call
        ``super()._registerProperties()`` first.
        '''
        self._minimum_current = getattr(self, '_minimum_current', 0.)
        self._maximum_current = getattr(self, '_maximum_current', 100.)
        self.registerProperty('current', ptype=float,
                              getter=lambda: float(self._command('RCS')),
                              setter=self._setCurrent,
                              minimum=0., maximum=100.,
                              debounce=500)
        self.registerProperty('maximum_current', ptype=float,
                              getter=lambda: self._maximum_current,
                              setter=self._setMaximumCurrent,
                              minimum=0., maximum=100.)
        self.registerProperty('aiming', ptype=bool,
                              getter=lambda: self._flagSet('AIM'),
                              setter=self._setAiming)
        self.registerProperty('emission', ptype=bool,
                              getter=lambda: self._flagSet('EMX'),
                              setter=self._setEmission)
        self.registerProperty('power', ptype=float, setter=None,
                              getter=self._getPower)
        self.registerProperty('power_supply', ptype=bool, setter=None,
                              getter=lambda: not self._flagSet('PWR'))
        self.registerProperty('keyswitch', ptype=bool, setter=None,
                              getter=lambda: self._flagSet('KEY'))
        self.registerProperty('fault', ptype=bool, setter=None,
                              getter=lambda: self._flagSet('ERR'))
        self.registerProperty('minimum_current', ptype=float, setter=None,
                              getter=lambda: self._minimum_current)
        self.registerProperty('firmware', ptype=str, setter=None,
                              getter=lambda: self._command('RFV'))
        self.registerProperty('temperature', ptype=float, setter=None,
                              getter=lambda: float(self._command('RCT')))

    def identify(self) -> bool:
        '''Return True if the connected device responds as an IPG laser.

        Queries the firmware version string (``RFV``) and checks that the
        response contains more than 3 characters.  On success, reads and
        caches ``minimum_current`` via ``RNC``.
        '''
        firmware = self._command('RFV')
        if len(firmware) <= 3:
            return False
        self._minimum_current = float(self._command('RNC'))
        return True

    def _command(self, cmd: str) -> str:
        '''Send a command and return the value portion of the echoed response.

        The IPG protocol echoes the command mnemonic before the value in
        every response (e.g. ``'ROP: 10.5'``).  If the mnemonic echo is
        present, returns the value token; otherwise returns the full
        response and logs an informational message.

        Commands that carry an argument (e.g. ``'SDC 50.0'``) are matched
        by their mnemonic only, so the argument does not interfere with
        the echo check.

        Parameters
        ----------
        cmd : str
            IPG command string, optionally followed by a value argument
            (e.g. ``'STA'``, ``'ABN'``, ``'SDC 50.0'``).

        Returns
        -------
        str
            Value token from the echoed response, or the full response
            if the mnemonic echo is absent.
        '''
        response = self.handshake(cmd)
        mnemonic = cmd.split()[0]
        if mnemonic not in response:
            logger.info(f'Unexpected response to {cmd!r}: {response!r}')
            return response
        parts = response.split()
        return parts[1] if len(parts) >= 2 else response

    def _flags(self) -> int:
        '''Return the raw instrument status word.'''
        return int(self._command('STA'))

    def _flagSet(self, flagname: str) -> bool:
        '''Return True if the named status flag is set.

        Parameters
        ----------
        flagname : str
            Key into :attr:`flag` (e.g. ``'KEY'``, ``'AIM'``).
        '''
        return bool(self._flags() & self.flag[flagname])

    def _getPower(self) -> float:
        '''Return current output power [W].

        The instrument responds with ``'Off'`` when emission is disabled,
        ``'Low'`` when power is below the measurable threshold, or a
        numeric string otherwise.
        '''
        value = self._command('ROP')
        if 'Off' in value:
            return 0.
        if 'Low' in value:
            return 0.1
        return float(value)

    def _setCurrent(self, v: float) -> None:
        '''Set the diode current setpoint, clamped to ``maximum_current``.

        Parameters
        ----------
        v : float
            Requested diode current [%].
        '''
        limit = self._maximum_current
        clamped = min(float(v), limit)
        if clamped < float(v):
            logger.warning(
                f'current {v:.1f}% exceeds maximum_current '
                f'{limit:.1f}%; clamped to {clamped:.1f}%')
        self._command(f'SDC {clamped:.1f}')

    def _setMaximumCurrent(self, v: float) -> None:
        '''Set the software upper bound on the diode current setpoint.

        Values outside [0, 100] are rejected and a warning is logged.

        Parameters
        ----------
        v : float
            New maximum diode current [%].
        '''
        v = float(v)
        if not 0. <= v <= 100.:
            logger.warning(
                f'maximum_current {v:.1f}% out of range [0, 100]; ignored')
            return
        self._maximum_current = v

    def _setAiming(self, state: bool) -> None:
        '''Enable or disable the aiming beam.

        Parameters
        ----------
        state : bool
            True to enable (``ABN``), False to disable (``ABF``).
        '''
        self._command('ABN' if bool(state) else 'ABF')

    def _setEmission(self, state: bool) -> None:
        '''Enable or disable laser emission.

        Parameters
        ----------
        state : bool
            True to enable (``EMON``), False to disable (``EMOFF``).
        '''
        self._command('EMON' if bool(state) else 'EMOFF')

    def status(self) -> dict[str, bool | float]:
        '''Return a snapshot of all polled status properties.

        Reads the status word (``STA``) and output power (``ROP``) once
        each, avoiding redundant ``STA`` queries.  Intended for use by
        the widget poll loop.

        Returns
        -------
        dict[str, bool | float]
            Mapping of property name to current value for
            ``power_supply``, ``keyswitch``, ``aiming``, ``emission``,
            ``fault``, and ``power``.
        '''
        flags = self._flags()
        return {
            'power_supply': not bool(flags & self.flag['PWR']),
            'keyswitch':    bool(flags & self.flag['KEY']),
            'aiming':       bool(flags & self.flag['AIM']),
            'emission':     bool(flags & self.flag['EMX']),
            'fault':        bool(flags & self.flag['ERR']),
            'power':        self._getPower(),
        }

    def fault_detail(self) -> list[str]:
        '''Return a list of active fault condition names.

        Returns an empty list when no faults are active.

        Returns
        -------
        list[str]
            Human-readable names of active fault conditions.  Possible
            values: ``'over-temperature'``, ``'excessive backreflection'``,
            ``'power supply off'``, ``'unexpected emission'``.
        '''
        flags = self._flags()
        conditions = [
            ('TMP', 'over-temperature'),
            ('BKR', 'excessive backreflection'),
            ('PWR', 'power supply off'),
            ('UNX', 'unexpected emission'),
        ]
        return [label for key, label in conditions if flags & self.flag[key]]


if __name__ == '__main__':
    QIPGLaser.example()

__all__ = ['QIPGLaser']
