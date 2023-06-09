from PyQt5.QtCore import (pyqtProperty, pyqtSlot)
from QInstrument.lib import QSerialInstrument
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class QOpus(QSerialInstrument):
    '''Quantum Opus 570nm Laser

    .....

    Inherits
    --------
    SerialInstrument

    Properties
    ----------
    portName: str
        Name of the serial port to which the laser is attached

    Methods
    -------
    get_power(): float
         Power of laser output [mW]
    set_power(float):
         Set Power [mW]
    '''

    settings = dict(baudRate=QSerialInstrument.Baud19200,
                    dataBits=QSerialInstrument.Data8,
                    stopBits=QSerialInstrument.OneStop,
                    parity=QSerialInstrument.NoParity,
                    flowControl=QSerialInstrument.NoFlowControl,
                    eol='\r')

    def __init__(self, portName=None, **kwargs):
        super().__init__(portName, **self.settings, **kwargs)

    def identify(self):
        return 'MPC-D-1.0.07A' in self.handshake('VERSION?')

    def Property(cmd, dtype=int, res='0'):
        def getter(self):
            logger.debug('Getting')
            return self.get_value(cmd, dtype=dtype)

        def setter(self, value):
            value = dtype(value)
            logger.debug(f'Setting {value}')
            self.expect(f'{cmd},{value}', res)
        return pyqtProperty(dtype, getter, setter)

    def keyswitch(self):
        return self.handshake('STATUS?')

    def get_status(self):
        if self.handshake('POWER?') == '0000.0mW':
            return 'Off'
        else:
            return 'On'

    def status(self, value):
        if value == 'disable':
            self.expect('OFF', '')
        if value == 'enable':
            self.expect('ON', '')
        else:
            return

    @pyqtSlot()
    def power(self):
        power = self.handshake('POWER?')
        return power

    def set_power(self, value):
        '''Sets power (mW)'''
        self.expect(f'POWER={value}', '')

    def current(self):
        return self.handshake('CURRENT?')

    def set_current(self, value):
        '''Sets current as percentage of maximum'''
        self.expect(f'CURRENT={value}', '')

    def lastemp(self):
        return self.handshake('LASTEMP?')

    def psutemp(self):
        return self.handshake('PSUTEMP?')

    def timers(self):
        '''Get the timers of the laser and PSU'''
        return self._read_timers('TIMERS?')

    @QSerialInstrument.blocking
    def _read_timers(self, query):
        self.transmit(query)
        response = []
        while True:
            this = self.read_until()
            response.append(this)
            if 'Hours' in this:
                pass
            else:
                break
        return response
