from QInstrument.lib import QSerialInstrument
from PyQt5.QtCore import pyqtProperty
from struct import unpack
import logging

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)


class QPDUS210(QSerialInstrument):
    settings = dict(baudRate=QSerialInstrument.Baud9600,
                    dataBits=QSerialInstrument.Data8,
                    stopBits=QSerialInstrument.OneStop,
                    parity=QSerialInstrument.NoParity,
                    flowControl=QSerialInstrument.NoFlowControl,
                    timeout=1000.,
                    eol='\r')

    def Property(pstr, dtype=int):
        def getter(self):
            return self.get_value(f'get{pstr}', dtype=dtype)

        def setter(self, value):
            value = int(value) if (dtype == bool) else dtype(value)
            self.send(f'set{pstr}{value}')

        return pyqtProperty(dtype, getter, setter)

    def GainProperty(gstr, sstr, dtype=int):
        def getter(self):
            return self.get_value(f'get{gstr}', dtype=dtype)

        def setter(self, value):
            value = int(value) if (dtype == bool) else dtype(value)
            self.send(f'set{sstr}{value}')

        return pyqtProperty(dtype, getter, setter)

    def Toggle(pstr):
        def getter(self):
            response = self.get_value(f'is{pstr}', dtype=str)
            return (response == 'TRUE')

        def setter(self, enable):
            if enable:
                cmd = 'ENABLE' if (pstr == 'ENABLE') else f'en{pstr}'
            else:
                cmd = 'DISABLE' if (pstr == 'ENABLE') else f'dis{pstr}'
            self.send(cmd)

        return pyqtProperty(int, getter, setter)

    def Measured(pstr, dtype=int):
        def getter(self):
            result = self.get_value(f'read{pstr}', dtype=dtype)
            return result

        return pyqtProperty(dtype, getter, fset=None)

    # Setpoints
    frequency = Property('FREQ', dtype=float)  # Hz
    targetVoltage = Property('VOLT')    # Volts pp
    maxFrequency = Property('MAXFREQ')
    minFrequency = Property('MINFREQ')
    targetPhase = Property('PHASE')
    maxLoadPower = Property('MAXLPOW')
    targetPower = Property('TARPOW')
    targetCurrent = Property('CURRENT')

    # Gain properties
    phaseGain = GainProperty('PHASEGAIN', 'GAINPHASE')
    powerGain = GainProperty('POWERGAIN', 'GAINPOWER')
    currentGain = GainProperty('CURRENTGAIN', 'GAINCURRENT')

    # Toggleable Settings
    phaseTracking = Toggle('PHASE')
    powerTracking = Toggle('POWER')
    currentTracking = Toggle('CURRENT')
    frequencyWrapping = Toggle('WRAP')
    enabled = Toggle('ENABLE')

    # Measurable Values
    phase = Measured('PHASE')
    impedance = Measured('IMP')
    loadPower = Measured('LPOW')
    amplifierPower = Measured('APOW')
    current = Measured('CURRENT')
    temperature = Measured('TEMP', dtype=float)  # Celsius

    def __init__(self, portName=None, **kwargs):
        super().__init__(portName, **self.settings, **kwargs)

    def identify(self):
        '''DISABLE returns FALSE to confirm the driver has been disabled, 
        and also defaults the driver to its (safer) disabled state'''
        return 'FALSE' in self.handshake('DISABLE')

    def save(self):
        '''Saves current parameters to permanent storage'''
        return self.handshake('SAVE')

    @pyqtProperty(dict)
    def state(self):
        '''Uses built-in feature to get all info from PDUS210 
        in one serial command'''
        self.blockSignals(True)
        self.send('getSTATE')
        data = self.readn(80)
        self.blockSignals(False)
        keys = ['enabled', 'phaseTracking', 'currentTracking', 'powerTracking',
                'errorAmp', 'errorLoad', 'errorTemperature',
                'voltage', 'frequency', 'minFrequency', 'maxFrequency',
                'targetPhase', 'phaseControlGain',
                'maxLoadPower', 'amplifierPower', 'loadPower',
                'temperature', 'measuredPhase', 'measuredCurrent',
                'impedance', 'transformerTurns']
        vals = unpack(data, '<7cx18f')
        state = dict(zip(keys, vals))
        return state
