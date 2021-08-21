from PyQt5.QtCore import (pyqtProperty, pyqtSignal, pyqtSlot)
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

    positionChanged = pyqtSignal(object)
    
    def Property(cmd, dtype=int):      
        def getter(self):
            return self.get_value(cmd, dtype=dtype)
        def setter(self, value):
            value = dtype(value)
            self.expect(f'{cmd},{value}', res)
        return pyqtProperty(dtype, getter, setter)

    speed         = Property('SMS')
    acceleration  = Property('SAS')
    scurve        = Property('SCS')
    zspeed        = Property('SMZ')
    zacceleration = Property('SAZ')
    zscurve       = Property('SCZ')

    def __init__(self, portName=None, **kwargs):
        super().__init__(portName, **self.settings, **kwargs)
        self._mirror = False
        self._flip = False

    def identify(self):
        return len(self.version()) == 3

    def version(self):
        '''Return 3-digit firmware version'''
        return self.handshake('VERSION')

    @pyqtSlot()
    def position(self):
        '''Report the (x, y, z) coordinates of the stage

        Returns
        -------
        position: list of int
           x, y, z coordinates of current stage position
        '''
        position = list(map(int, self.handshake('P').split(',')))
        self.positionChanged.emit(position)
        return position

    def set_position(self, position):
        position = ','.join(map(str, position))
        return self.expect(f'P,{position}', '0')

    @pyqtSlot()
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

    def set_velocity(self, velocity):
        '''Virtual joystick move'''
        velocity = ','.join(map(str, velocity))
        self.send(f'VS,{velocity}')

    def stop(self):
        '''Stop stage motion'''
        return self.expect('I', 'R')

    def status(self):
        return self.get_value('$', dtype=int)

    @pyqtProperty(bool)
    def moving(self):
        '''True if stage or focus are in motion'''
        return bool(self.status() & 0xF)

    @pyqtProperty(bool)
    def flip(self):
        return self._flip

    @flip.setter
    def flip(self, value):
        self._flip = value
        c = -1 if value else 1
        self.expect(f'YD,{c}', '0')
    
    @pyqtProperty(bool)
    def mirror(self):
        return self._mirror

    @mirror.setter
    def mirror(self, value):
        self._mirror = value
        c = -1 if value else 1
        self.expect(f'XD,{c}', '0')
    
    @pyqtProperty(float)
    def resolution(self):
        return self.get_value('RES,s')

    @resolution.setter
    def resolution(self, value):
        '''Get and set the resolution for the stage in micrometers'''
        self.send(f'RES,s,{value}')

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
        self.blockSignals(True)
        self.send(query)
        response = []
        while True:
            this = self.read_until()
            response.append(this)
            if 'END' in this:
                break
        self.blockSignals(False)
        return response
