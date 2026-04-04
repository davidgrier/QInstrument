import logging
from QInstrument.lib.QSerialInstrument import QSerialInstrument


logger = logging.getLogger(__name__)


class QIPGLaser(QSerialInstrument):
    '''IPG Photonics YLR Ytterbium Fiber Laser

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
    aiming : bool
        True: aiming beam on. False: aiming beam off.
    emission : bool
        True: laser emission enabled. False: emission off.

    Status (read-only)
    ------------------
    fault : bool
        True: one or more fault conditions are active.
        Fault conditions: over-temperature, excessive backreflection,
        power supply off, unexpected emission detected.
    keyswitch : bool
        True: keyswitch in REM (remote) position.
    power : float [W]
        Current output power.
    '''

    flag = {'ERR': 0x1,
            'TMP': 0x2,       # over-temperature condition
            'EMX': 0x4,       # laser emission active
            'BKR': 0x8,       # excessive backreflection
            'ACL': 0x10,      # analog control mode enabled
            'MDC': 0x40,      # module communication disconnected
            'MFL': 0x80,      # module(s) failed
            'AIM': 0x100,     # aiming beam on
            'PWR': 0x800,     # power supply off
            'MOD': 0x1000,    # modulation enabled
            'ENA': 0x4000,    # laser enable asserted
            'EMS': 0x8000,    # emission startup
            'UNX': 0x20000,   # unexpected emission detected
            'KEY': 0x200000}  # keyswitch in REM position

    comm = dict(baudRate=QSerialInstrument.BaudRate.Baud57600,
                dataBits=QSerialInstrument.DataBits.Data8,
                stopBits=QSerialInstrument.StopBits.OneStop,
                parity=QSerialInstrument.Parity.NoParity,
                flowControl=QSerialInstrument.FlowControl.NoFlowControl,
                eol='\r')

    def __init__(self, portName: str | None = None, **kwargs) -> None:
        super().__init__(portName, **(self.comm | kwargs))
        self.flag['ERR'] = (self.flag['TMP'] | self.flag['BKR'] |
                            self.flag['PWR'] | self.flag['UNX'])
        self._registerProperties()

    def _registerProperties(self) -> None:
        '''Register all instrument properties via ``registerProperty()``.

        Called once from ``__init__``. Subclasses that extend the property
        set should call ``super()._registerProperties()`` first.
        '''
        self.registerProperty('keyswitch', ptype=bool, setter=None,
                              getter=lambda: self._flagSet('KEY'))
        self.registerProperty('aiming', ptype=bool,
                              getter=lambda: self._flagSet('AIM'),
                              setter=self._setAiming)
        self.registerProperty('emission', ptype=bool,
                              getter=lambda: self._flagSet('EMX'),
                              setter=self._setEmission)
        self.registerProperty('power', ptype=float, setter=None,
                              getter=self._getPower)
        self.registerProperty('fault', ptype=bool, setter=None,
                              getter=lambda: self._flagSet('ERR'))

    def identify(self) -> bool:
        '''Return True if the connected device responds as an IPG laser.

        Queries the firmware version string (``RFV``) and checks that the
        response contains more than 3 characters.
        '''
        return len(self._command('RFV')) > 3

    def _command(self, cmd: str) -> str:
        '''Send a command and return the value portion of the echoed response.

        The IPG protocol echoes the command name before the value in every
        response (e.g. ``'ROP 10.5'``).  If the echo is present, returns
        the value token; otherwise returns the full response and logs an
        informational message.

        Parameters
        ----------
        cmd : str
            IPG command mnemonic (e.g. ``'STA'``, ``'ABN'``).
        '''
        response = self.handshake(cmd)
        if cmd not in response:
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

    def version(self) -> str:
        '''Return the firmware version string.'''
        return self._command('RFV')

    def current(self) -> tuple[float, float, float]:
        '''Return diode current readings [A].

        Returns
        -------
        tuple[float, float, float]
            (actual, minimum, setpoint) diode currents.
        '''
        cur = float(self._command('RDC'))
        minimum = float(self._command('RNC'))
        setpoint = float(self._command('RCS'))
        return cur, minimum, setpoint

    def temperature(self) -> float:
        '''Return the laser diode temperature [°C].'''
        return float(self._command('RCT'))


if __name__ == '__main__':
    QIPGLaser.example()

__all__ = ['QIPGLaser']
