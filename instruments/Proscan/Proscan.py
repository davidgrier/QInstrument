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

    def __init__(self, portName=None, **kwargs):
        super().__init__(portName, **self.settings, **kwargs)
        self._muted = False

    def identify(self):
        return 'PROSCAN' in self.handshake('DATE').upper()

