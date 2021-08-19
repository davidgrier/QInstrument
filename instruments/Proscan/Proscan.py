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

    def position(self):
        return list(map(int, self.handshake('P').split(',')))

    def version(self):
        return self.handshake('VERSION')
    
    def read_lines(self, query):
        self.send(query)
        response = []
        while True:
            this = self.read_until()
            response.append(this)
            if 'END' in this:
                break
        return response

    def describe(self):
        return self.read_lines('?')

    def stage(self):
        return self.read_lines('STAGE')

    def focus(self):
        return self.read_lines('FOCUS')
