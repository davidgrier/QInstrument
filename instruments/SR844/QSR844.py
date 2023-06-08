from PyQt5.QtCore import (pyqtProperty, pyqtSlot)
from QInstrument.lib.QSerialInstrument import QSerialInstrument


class QSR844(QSerialInstrument):
    '''SRS SR844 Lockin Amplifier

    .....

    Inherits
    --------
    SerialInstrument

    Properties
    ==========
    Setting properties on an instantiated object
    changes corresponding settings on the connected
    instrument.

    Reference and Phase
    -------------------
    frequency: float
        Reference frequency for internal oscillator [Hz]
        Rounded to 5 digits or 0.0001 Hz, whichever is greater.
        Range: 0.001 <= frequency, frequency*harmonic <= 102 kHz
    harmonic: int
        Detection harmonic.
        Range: 1 <= harmonic < 20000, frequency*harmonic <= 102 kHz
    internal_reference: bool
        True: use internal reference source
        False: use external reference source
    phase: float
        Reference phase shift [degrees]
        Range: -360 degrees <= phase <= 729.99 degrees, mod 180 degrees
    reference_impedance: int
        Reference input impedance
        0: 50 Ohm
        1: 10 kOhm

    Signal Input
    ------------
    input_impedance: int
        0: 50 Ohm
        1: 1 MOhm

    wide_reserve: int
        Wide reserve mode
        0: High dynamic reserve
        1: Normal
        2: Low

    Gain and Time Constant
    ----------------------
    close_reserve: int
        0: High dynamic reserve, suitable for noisy signals
        1: Normal dynamic reserve
        2: Low noise
    low_pass_slope: int
        0:  6 dB/octave
        1: 12 dB/octave
        2: 18 dB/octave
        3: 24 dB/octave
    sensitivity: int
        0: 100 nVrms / -127 dBm   8:   1 mVrms / -47 dBm
        1: 300 nVrms / -117 dBm   9:   3 mVrms / -37 dBm
        2:   1 uVrms / -107 dBm  10:  10 mVrms / -27 dBm
        3:   3 uVrms /  -97 dBm  11:  30 mVrms / -17 dBm
        4:  10 uVrms /  -87 dBm  12: 100 mVrms /  -7 dBm
        5:  30 uVrms /  -77 dBm  13: 300 mVrms /  +3 dBm
        6: 100 uVrms /  -67 dBm  14:   1  Vrms / +13 dBm
        7: 300 uVrms /  -57 dBm
    time_constant: int
        Input filter time constant
        0: 100 us     9:   3 s
        1: 300 us    10:  10 s
        2:   1 ms    11:  30 s
        3:   3 ms    12: 100 s
        4:  10 ms    13: 300 s
        5:  30 ms    14:   1 ks
        6: 100 ms    15:   3 ks
        7: 300 ms    16:  10 ks
        8:   1 s    17:  30 ks

    Methods
    =======
    report(): [float, float, float]
        Returns frequency, amplitude and phase
    reset():
        Reset instrument to default settings
    '''

    comm = dict(baudRate=QSerialInstrument.Baud9600,
                dataBits=QSerialInstrument.Data8,
                stopBits=QSerialInstrument.OneStop,
                parity=QSerialInstrument.NoParity,
                flowControl=QSerialInstrument.NoFlowControl,
                eol='\r')

    def Property(pstr, dtype=int):
        def getter(self):
            response = self.handshake(f'{pstr}?')
            try:
                value = dtype(response)
            except ValueError:
                value = None
            return value

        def setter(self, value):
            if dtype == bool:
                value = int(value)
            self.transmit(f'{pstr}{value}')

        return pyqtProperty(dtype, getter, setter)

    # Reference and Phase
    frequency = Property('FREQ', float)
    harmonic = Property('HARM')
    internal_reference = Property('FMOD', bool)
    phase = Property('PHAS', float)
    reference_impedance = Property('REFZ')
    # Input Signal
    wide_reserve = Property('WRSV')
    input_impedance = Property('INPZ')
    # Gain and Time Constant
    sensitivity = Property('SENS')
    close_reserve = Property('CRSV')
    low_pass_slope = Property('OFSL')
    time_constant = Property('OFLT')

    def __init__(self, portName=None, **kwargs):
        super().__init__(portName, **self.comm, **kwargs)

    def identify(self):
        return 'SR844' in self.handshake('*IDN?')

    def report(self):
        response = self.handshake('SNAP?9,3,4')
        return list(map(float, response.split(',')))

    @pyqtProperty(int)
    def reference_frequency(self):
        return int(self.handshake('FRAQ?'))

    @pyqtProperty(int)
    def if_frequency(self):
        return int(self.handshake('FRIQ?'))

    @pyqtSlot()
    def reset(self):
        self.transmit('*RST')

    @pyqtSlot()
    def auto_gain(self):
        '''Autorange gain'''
        self.transmit('AGAN')

    @pyqtSlot()
    def auto_close_reserve(self):
        '''Autorange close dynamic reserve'''
        self.transmit('ACRS')

    @pyqtSlot()
    def auto_wide_reserve(self):
        '''Autorange wide dynamic reserve'''
        self.transmit('AWRS')

    @pyqtSlot()
    def auto_phase(self):
        '''Autorange phase'''
        self.transmit('APHS')

    @pyqtSlot()
    def auto_offset(self, channel):
        '''Autorange offset'''
        self.transmit('AOFF{channel}')


def example():
    from PyQt5.QtCore import QCoreApplication

    app = QCoreApplication([])
    lockin = QSR844().find()
    print(lockin)


if __name__ == '__main__':
    example()
