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
    current : float [%]
        Diode current as a percentage of maximum.
    emission : bool
        True: laser emission enabled. False: emission disabled.
    power : float [mW]
        Getter returns the actual output power.
        Setter transmits a new power setpoint.

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
                eol='\r')

    def _registerProperties(self) -> None:
        '''Register all instrument properties via ``registerProperty()``.

        Called once from ``__init__``. Subclasses that extend the property
        set should call ``super()._registerProperties()`` first.
        '''
        self.registerProperty('power', ptype=float,
                              getter=self._getPower,
                              setter=lambda v: self.transmit(f'POWER={float(v)}'))
        self.registerProperty('current', ptype=float,
                              getter=self._getCurrent,
                              setter=lambda v: self.transmit(f'CURRENT={float(v)}'))
        self.registerProperty('emission', ptype=bool,
                              getter=lambda: self._getPower() > 0,
                              setter=self._setEmission)
        self.registerProperty('laser_temperature', ptype=float, setter=None,
                              getter=lambda: self._parseTemp('LASTEMP?'))
        self.registerProperty('psu_temperature', ptype=float, setter=None,
                              getter=lambda: self._parseTemp('PSUTEMP?'))

    def identify(self) -> bool:
        '''Return True if the connected device identifies as an Opus laser.

        Queries the firmware version (``VERSION?``) and checks for the
        ``'MPC-D'`` controller model token in the response.
        '''
        return 'MPC-D' in self.handshake('VERSION?')

    def _getPower(self) -> float:
        '''Query and return the actual output power [mW].

        The instrument responds with a value and ``mW`` suffix
        (e.g. ``'0123.4mW'``).
        '''
        return float(self.handshake('POWER?').rstrip('mW'))

    def _getCurrent(self) -> float:
        '''Query and return the diode current [%].

        The instrument responds with a value and ``%`` suffix
        (e.g. ``'050.0%'``).
        '''
        return float(self.handshake('CURRENT?').rstrip('%'))

    def _parseTemp(self, cmd: str) -> float:
        '''Query a temperature command and return the value [°C].

        Strips trailing unit characters (``C``, ``°``) before conversion.

        Parameters
        ----------
        cmd : str
            Temperature query mnemonic (``'LASTEMP?'`` or ``'PSUTEMP?'``).
        '''
        return float(self.handshake(cmd).rstrip(' C°'))

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
