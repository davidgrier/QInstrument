from PyQt5.QtCore import (pyqtProperty, pyqtSignal, pyqtSlot)
from QInstrument.lib import SerialInstrument
import numpy as np
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class Opus(SerialInstrument):
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

    settings = dict(baudRate=SerialInstrument.Baud19200,
                    dataBits=SerialInstrument.Data8,
                    stopBits=SerialInstrument.OneStop,
                    parity=SerialInstrument.NoParity,
                    flowControl=SerialInstrument.NoFlowControl,
                    eol='\r')
    def __init__(self, portName=None, **kwargs):
        super().__init__(portName, **self.settings, **kwargs)
        self._status = False

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
        return float(self.handshake('STATUS?'))
    
    @pyqtProperty(bool)
    def status(self):
        return self._status
    
    @status.setter
    def status(self, value):
        if value == self._status:
            return
        if value == OFF:
            self.send('OFF')
            self._status = OFF
        else:
            self.send('ON')
            self._status = ON
            
    @pyqtProperty(float)
    def power(self):
        return self.handshake('POWER?')
        
    @power.setter
    def power(self, value):
        '''Sets power (mW)'''
        self.send('POWER={value}')
        
    @pyqtProperty(float)
    def current(self):
        return self.handshake('CURRENT?')
        
    @current.setter
    def current(self, value):
        '''Sets current as percentage of maximum'''
        self.send('CURRENT={value}')
        
    #@pyqtProperty(float)
    #def startPower(self)
        #'''Get default start-up power (mW)'''
        #return self.handshake('STPOW?')
    
    #@startPower.setter
    #def startPower(self, value)
        #'''Set default start-up power (mW)'''
        #self.send('STPOW={VALUE}')
        
            
    def get_lastemp(self):
        return self.handshake('LASTEMP?')
        
    def get_psutemp(self):
        return self.handshake('PSUTEMP?')
        
    def get_timers(self):
        '''Get the timers of the laser and PSU'''
        return self.handshake('TIMERS?')
        
    @SerialInstrument.blocking
    def _read_lines(self, query):
        self.send(query)
        response = []
        while True:
            this = self.read_until()
            response.append(this)
            if 'END' in this:
                break
        return response
