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
                    eol='\n')

    def Property(gstr, sstr, response='R', dtype=int):      
        @pyqtProperty(dtype)
        def prop(self):
            return self.get_value(f'{gstr}', dtype=dtype)
        @prop.setter
        def prop(self, value):
            self._error = response not in self.handshake(f'{sstr} {value}')
        return prop

    Property(x, 'PX', response='0')
    Property(y, 'PY', response='0')
    Property(z, 'PZ', response='0')
    Property(position, 'P', response='0')
    Property(step_size, 'X', response='0')

    def __init__(self, portName=None, **kwargs):
        super().__init__(portName, **self.settings, **kwargs)
        self._muted = False

    def identify(self):
        return 'PROSCAN' in self.handshake('DATE')
