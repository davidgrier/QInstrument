from PyQt5.QtCore import pyqtProperty
from QInstrument.lib import SerialInstrument


class SR830(SerialInstrument):
    '''SRS SR830 Lockin Amplifier

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
    output_amplitude: int
        Amplitude of reference sine output [V]
        Rounted to 0.002V.
        Range: 0.004V <= output_amplitude <= 5.000V
    phase: float
        Reference phase shift [degrees]
        Range: -360 degrees <= phase <= 729.99 degrees, mod 180 degrees
    reference_trigger: int
        Select reference trigger for external reference
        0: sine zero crossing
        1: TTL rising edge
        2: TTL falling edge
        Must be set to either 1 or 2 when frequency < 1 Hz.
    
    Input and Filter
    ----------------
    dc_coupling: bool
        True: inputs use DC coupling
        False: inputs use AC coupling
    input_configuration: int
        0: channel A
        1: A - B
        2: I (1 Mohm)
        3: I (100 Mohm)
    line_filter: int
        Input line notch filter configuration
        0: no filters
        1: use line notch filter
        2: use 2x line notch filter
        3: use both notch filters
    shield_grounding: bool
        True: input shielding is grounded
        False: input shielding is floating

    Gain and Time Constant
    ----------------------
    dynamic_reserve: int
        0: High dynamic reserve, suitable for noisy signals
        1: Normal dynamic reserve
        2: Low noise
    low_pass_slope: int
        0:  6 dB/octave
        1: 12 dB/octave
        2: 18 dB/octave
        3: 24 dB/octave
    sensitivity: int
        0:   2 nV/fA    10:   5 uV/pA    20:  10 mV/nA
        1:   5 nV/fA    11:  10 uV/pA    21:  20 mV/nA
        2:  10 nV/fA    12:  20 uV/pA    22:  50 mV/nA
        3:  20 nV/fA    13:  50 uV/pA    23: 100 mV/nA
        4:  50 nV/fA    14: 100 uV/nA    24: 200 mV/nA
        5: 100 nV/fA    15: 200 uV/nA    25: 500 mV/nA
        6: 200 nV/fA    16: 500 uV/nA    26:   1 V/uA
        7: 500 nV/fA    17:   1 mV/nA
        8:   1 uV/pA    18:   2 mV/nA
        9:   2 uV/pA    19:   5 mV/nA
    synchronous_filter: bool
        True: synchronous filtering below 200 Hz
            Only engaged if harmonic * frequency < 200 Hz
        False: no synchronous filter
    time_constant: int
        Input filter time constant
        0:  20 us    10:   1 s
        1:  30 us    11:   3 s
        2: 100 us    12:  10 s
        3: 300 us    13:  30 s
        4:   1 ms    14: 100 s
        5:   3 ms    15: 300 s
        6:  10 ms    16:   1 ks
        7:  30 ms    17:   3 ks
        8: 100 ms    18:  10 ks
        9: 300 ms    19:  30 ks

    Methods
    =======
    report(): [float, float, float]
        Returns frequency, amplitude and phase
    reset():
        Reset instrument to default settings
    '''

    settings = dict(baudRate=SerialInstrument.Baud9600,
                    dataBits=SerialInstrument.Data8,
                    stopBits=SerialInstrument.OneStop,
                    parity=SerialInstrument.NoParity,
                    flowControl=SerialInstrument.NoFlowControl,
                    eol='\n')

    def Property(pstr, dtype=int):      
        @pyqtProperty(dtype)
        def prop(self):
            return self.get_value(f'{pstr}?', dtype=dtype)
        @prop.setter
        def prop(self, value):
            if dtype == bool:
                value = int(value)
            self.send(f'{pstr}{value}')
        return prop

    # Reference and Phase
    frequency = Property('FREQ', float)
    harmonic = Property('HARM')
    internal_reference = Property('FMOD', bool)
    output_amplitude = Property('SLVL', float)
    phase = Property('PHAS', float)
    reference_trigger = Property('RSLP')
    # Input and Filter
    dc_coupling = Property('ICPL', bool)
    input_configuration = Property('ISRC')
    line_filter = Property('ILIN')    
    shield_grounding = Property('IGND', bool)
    # Gain and Time Constant
    dynamic_reserve = Property('RMOD')
    low_pass_slope = Property('OFSL')
    sensitivity = Property('SENS')
    synchronous_filter = Property('SYNC', bool)
    time_contant = Property('OFLT')

    def __init__(self, portName=None, **kwargs):
        super().__init__(portName, **self.settings, **kwargs)

    def identify(self):
        return 'SR830' in self.handshake('*IDN?')

    def reset(self):
        self.send('*RST')

    def report(self):
        return list(map(float, self.handshake('SNAP?9,3,4').split(',')))

    def auto_gain(self):
        self.send('AGAN')

    def auto_reserve(self):
        self.send('ARSV')

    def auto_phase(self):
        self.send('APHS')

    def auto_offset(self, channel):
        self.send('AOFF{channel}')
