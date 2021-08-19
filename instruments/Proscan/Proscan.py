from PyQt5.QtCore import pyqtProperty
from QInstrument.lib import SerialInstrument
import numpy as np


class Proscan(SerialInstrument):
    '''Prior Proscan Microscope Stage Controller

    .....

    Inherits
    --------
    SerialInstrument

    Properties
    ==========
    Setting properties on an instantiated object
    changes corresponding settings on the connected
    instrument.
    '''

    settings = dict(baudRate=SerialInstrument.Baud9600,
                    dataBits=SerialInstrument.Data8,
                    stopBits=SerialInstrument.OneStop,
                    parity=SerialInstrument.NoParity,
                    flowControl=SerialInstrument.NoFlowControl,
                    eol='\r')

    def __init__(self, portName=None, **kwargs):
        super().__init__(portName, **self.settings, **kwargs)
        self._muted = False

    def identify(self):
        return len(self.version()) == 3

    def version(self):
        '''Return 3-digit firmware version'''
        return self.handshake('VERSION')

    def position(self):
        '''Report the (x, y, z) coordinates of the stage

        Returns
        -------
        position: list of int
           x, y, z coordinates of current stage position
        '''
        return list(map(int, self.handshake('P').split(',')))

    def set_origin(self):
        '''Set the origin of the coordinate system

        Returns
        -------
        success: bool
             True: origin set to current position
             False: communication error
        '''
        return self.expect('Z', '0')

    def move_to(self, position, relative=False):
        cmd = 'GR' if relative else 'G'
        coordinates = ','.join(map(str, position))
        return self.expect(f'{cmd},{coordinates}', 'R')

    def move_to_origin(self):
        return self.expect('M', 'R')

    @pyqtProperty(float)
    def resolution(self):
        return float(self.handshake('RES,X'))

    @resolution.setter
    def resolution(self, value):
        '''Get and set the resolution for the stage in micrometers'''
        self.send(f'RES,s,{value}')

    @pyqtProperty(int)
    def speed(self):
        return int(self.handshake('SMS'))

    @speed.setter
    def speed(self, value):
        return self.expect(f'SMS,{value}', '0')
    
    @pyqtProperty(int)
    def acceleration(self):
        return int(self.handshake('SAS'))

    @acceleration.setter
    def acceleration(self, value):
        '''Maximum acceleration of stage in range [1, 100]'''
        return self.expect(f'SAS,{value}', '0')

    @pyqtProperty(int)
    def scurve(self):
        return int(self.handshake('SCS'))

    @scurve.setter
    def scurve(self, value):
        return self.expect(f'SCS,{value}', '0')

    def stop(self):
        '''Stop stage motion'''
        return self.expect('I', 'R')
    
    def description(self):
        '''Description of Proscan hardware'''
        return self._read_lines('?')

    def stage(self):
        '''Description of stage'''
        return self._read_lines('STAGE')

    def focus(self):
        '''Description of focus system'''
        return self._read_lines('FOCUS')

    def _read_lines(self, query):
        self.send(query)
        response = []
        while True:
            this = self.read_until()
            response.append(this)
            if 'END' in this:
                break
        return response
