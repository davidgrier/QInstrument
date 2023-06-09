from PyQt5.QtCore import (pyqtProperty, pyqtSignal, pyqtSlot)
from QInstrument.lib import QSerialInstrument
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class QProscan(QSerialInstrument):
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

    stepsize: float
        size of single stage step [um]
    speed: int
        maximum stage speed in range [1, 100]
    acceleration: int
        maximum stage acceleration in range [1, 100]
    scurve: int
        time derivative of stage acceleration in range [1, 100]

    zstepsize: float
        size of single focus step [um]
    zspeed: int
        maximum focus speed in range [1, 100]
    zacceleration: int
        maximum focus acceleration in range [1, 100]
    zscurve: int
        time derivative of focus acceleration in range [1, 100]

    '''

    settings = dict(baudRate=QSerialInstrument.Baud9600,
                    dataBits=QSerialInstrument.Data8,
                    stopBits=QSerialInstrument.OneStop,
                    parity=QSerialInstrument.NoParity,
                    flowControl=QSerialInstrument.NoFlowControl,
                    eol='\r')

    positionChanged = pyqtSignal(object)

    def Property(cmd, dtype=int, res='0'):
        def getter(self):
            logger.debug('Getting')
            return self.get_value(cmd, dtype=dtype)

        def setter(self, value):
            value = dtype(value)
            logger.debug(f'Setting {value}')
            self.expect(f'{cmd},{value}', res)
        return pyqtProperty(dtype, getter, setter)

    speed = Property('SMS')
    acceleration = Property('SAS')
    scurve = Property('SCS')
    zstepsize = Property('C', dtype=float)
    zspeed = Property('SMZ')
    zacceleration = Property('SAZ')
    zscurve = Property('SCZ')

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
        '''Define coordinates of present position

        Arguments
        ---------
        position: (x, y, [z])
            coordinates of present position in micrometers

        Returns
        -------
        success: bool
            True: position set successfully
        '''
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

    @pyqtProperty(float)
    def stepsize(self):
        return list(map(float, self.handshake('X').split(',')))[0]

    @stepsize.setter
    def stepsize(self, value):
        self.expect(f'X,{value},{value}', '0')

    def move_to(self, position, relative=False):
        '''Move stage to specified position

        Arguments
        ---------
        position: (x, y)
            Initiates stage motion to specified position
            using the current scurve, acceleration and speed
            settings. Coordinates are specified in micrometers.
        relative: bool [optional]
            True: Move by (x, y) relative to current position.
            False: Move to absolute position [Default]
        '''
        cmd = 'GR' if relative else 'G'
        coordinates = ','.join(map(str, position))
        return self.expect(f'{cmd},{coordinates}', 'R')

    def move_to_origin(self):
        '''Move stage to origin'''
        return self.expect('M', 'R')

    @pyqtSlot(object)
    def set_velocity(self, velocity):
        '''Initiate stage motion with specified velocity

        Arguments
        ---------
        velocity: (vx, vy)
            Start stage motion with velocity vx along the x axis
            and vy along the y axis. Velocity components are
            specified in micrometers per second.

        Note: set_velocity([0, 0]) stops the motion
        '''
        velocity = ','.join(map(str, velocity))
        self.expect(f'VS,{velocity}', 'R')

    @pyqtSlot()
    def stop(self):
        '''Stop stage motion'''
        logger.debug('STOP')
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
        self.transmit(f'RES,s,{value}')

    def stepLeft(self):
        '''Step stage left'''
        return self.expect('L', 'R')

    def stepRight(self):
        '''Step stage right'''
        return self.expect('R', 'R')

    def stepForward(self):
        '''Step stage forward'''
        return self.expect('F', 'R')

    def stepBackward(self):
        '''Step stage backward'''
        return self.expect('B', 'R')

    def stepUp(self):
        '''Step focus up'''
        return self.expect('U', 'R')

    def stepDown(self):
        '''Step focus down'''
        return self.expect('D', 'R')

    def description(self):
        '''Description of Proscan hardware'''
        return self._read_lines('?')

    def stage(self):
        '''Description of stage'''
        return self._read_lines('STAGE')

    def focus(self):
        '''Description of focus system'''
        return self._read_lines('FOCUS')

    @QSerialInstrument.blocking
    def _read_lines(self, query):
        self.transmit(query)
        response = []
        while True:
            this = self.read_until()
            response.append(this)
            if 'END' in this:
                break
        return response
