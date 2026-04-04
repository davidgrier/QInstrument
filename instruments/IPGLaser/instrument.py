import logging
from QInstrument.lib.QSerialInstrument import QSerialInstrument


logger = logging.getLogger(__name__)


class QIPGLaser(QSerialInstrument):
    '''IPG Ytterbium Fiber Laser

    Inherits
    --------
    QSerialInstrument

    Properties
    ==========
    aiming: bool
        True: aiming beam on. False: aiming beam off.
    emission: bool
        True: laser emission enabled. False: emission off.
    power: float [read-only]
        Current output power [W].
    keyswitch: bool [read-only]
        True: keyswitch in REM (remote) position.
    fault: bool [read-only]
        True: one or more fault conditions active.
        Fault conditions: over-temperature, excessive backreflection,
        power supply off, unexpected emission detected.
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

    def __init__(self, portName=None, **kwargs):
        super().__init__(portName, **(self.comm | kwargs))
        self.flag['ERR'] = (self.flag['TMP'] | self.flag['BKR'] |
                            self.flag['PWR'] | self.flag['UNX'])
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

    def identify(self):
        return len(self._command('RFV')) > 3

    def _command(self, cmd):
        '''Send a command and return the value portion of the echoed response.'''
        response = self.handshake(cmd)
        if cmd not in response:
            logger.info(f'Unexpected response to {cmd!r}: {response!r}')
            return response
        parts = response.split()
        return parts[1] if len(parts) >= 2 else response

    def _flags(self):
        return int(self._command('STA'))

    def _flagSet(self, flagname):
        return bool(self._flags() & self.flag[flagname])

    def _getPower(self):
        value = self._command('ROP')
        if 'Off' in value:
            return 0.
        if 'Low' in value:
            return 0.1
        return float(value)

    def _setAiming(self, state):
        self._command('ABN' if bool(state) else 'ABF')

    def _setEmission(self, state):
        self._command('EMON' if bool(state) else 'EMOFF')

    def version(self):
        '''Return firmware version string.'''
        return self._command('RFV')

    def current(self):
        '''Return (actual, minimum, setpoint) diode current [A].'''
        cur = float(self._command('RDC'))
        minimum = float(self._command('RNC'))
        setpoint = float(self._command('RCS'))
        return cur, minimum, setpoint

    def temperature(self):
        '''Return laser diode temperature [C].'''
        return float(self._command('RCT'))


if __name__ == '__main__':
    QIPGLaser.example()

__all__ = ['QIPGLaser']
