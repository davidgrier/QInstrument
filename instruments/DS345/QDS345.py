from PyQt5.QtCore import (pyqtProperty, pyqtSlot)
from QInstrument.lib import QSerialInstrument
import numpy as np
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)


class QDS345(QSerialInstrument):
    '''SRS DS345 Function Generator

    .....

    Inherits
    --------
    SerialInstrument

    Properties
    ==========
    Setting properties on an instantiated object
    changes corresponding settings on the connected
    instrument.

    Function Output
    ---------------
    amplitude: float
        Peak-to-peak amplitude of output signal [V]
        Range: 0. <= amplitude <= 5V, amplitude + offset <= 5V
    frequency: float
        Frequency of output signal [Hz]
        Range:
        sine:       1 uHz,      30.2 MHz
        square:     1 uHz,      30.2 MHz
        triangle:   1 uHz,     100.0 kHz
        ramp:       1 uHz,     100.0 kHz
        arbitrary:  2.329 mHz,  40.0 MHz sampling
        noise:     10 MHz white noise (fixed)
    invert: bool
        True: invert output.
        False: normal output.
    mute: bool
        True: mute output.
        False: restore last amplitude setting.
    offset: float
        DC output offset voltage [V]
        Range: 0 V <= offset <= 5V, amplitude + offset <= 5V
    phase: float
        Relative phase of output waveform [degrees]
        Range: 0.001 degrees <= phase <= 7199.999 degrees
        Note: Setting phase produces an error if
        waveform is set to noise (4) or arbitrary (5)
        or if a frequency sweep or frequency modulation
        is enabled.
    waveform: int
        Output waveform.
        0: sine
        1: square
        2: triangle
        3: ramp
        4: noise
        5: arbitrary waveform

    Output Modulation
    -----------------
    modulation: bool
        True: enable output modulation
        False: unmodulated output
    modulation_type: int
        0: linear sweep
        1: logarithmic sweep
        2: internal amplitude modulation
        3: frequency modulation
        4: phase modulation
        5: burst mode
    modulation_waveform: int
        Waveform used to modulate output:
        0: single sweep
        1: ramp
        2: triangle
        3: sine
        4: square
        5: arbitrary waveform
        6: none: used for burst mode modulation
        Note: arbitrary (5) may only be set for
        amplitude modulation (AM), frequency modulation (FM)
        or phase modulation (PM). The waveform must be
        loaded before setting modulation_waveform=5 and
        modulation=True or else an error will be produced.
    modulation_rate: float
        Modulation rate [Hz]
        Range: 0.001 Hz <= modulation_rate <= 10 kHz
        Value is rounded to 2 significant digits.
    burst_count: int
        Range: 1 <= burst_count <= 30000, subject to the
        constraint that the burst time cannot exceed 500s.
    am_depth: int
        Depth of AM modulation [percent]
        Range: 0 <= am_depth <= 100
        Note: negative values enable double-sideband-suppressed
        carrier modulation (DSBSC).
    fm_span: float
        Span of frequency modulation [Hz]
    pm_span: float
        Span of phase modulation_waveform [degrees]
        Range: 0 <= pm_span <= 7199.999 degrees
        Note: the phase shift ranges from -pm_span/2 to +pm_span/2
    sweep_center_frequency: float
        Sweep center frequency [Hz]
        Range: 0 <= sweep_center_frequency <= waveform limit
    sweep_span: float
        Sweep span [Hz]
        Range: abs(sweep_span) <= 2*sweep_center_frequency
        Note: negative values correspond to downward sweep.
    sweep_start_frequency: float
        Starting frequency for frequency sweep [Hz]
        Range: 0 <= sweep_start_frequency <= waveform maximum
    sweep_stop_frequency: float
        Ending frequency for frequency sweep [Hz]
        Range: 0 <= sweep_stop_frequency <= waveform maximum
    trigger_rate: float
        Rate for internally triggered bursts or sweeps [Hz]
        Range: 0.001 Hz <= trigger_rate <= 10 kHz
        Rounded to two significant digits.
    trigger_source: int
        Trigger source for bursts and sweeps
        0: single trigger: see trigger()
        1: internal rate
        2: external, positive slope
        3: external, negative slope
        4: line trigger

    Arbitrary Waveform
    ------------------
    sampling_frequency: float
    '''

    settings = dict(baudRate=QSerialInstrument.Baud9600,
                    dataBits=QSerialInstrument.Data8,
                    stopBits=QSerialInstrument.OneStop,
                    parity=QSerialInstrument.NoParity,
                    flowControl=QSerialInstrument.NoFlowControl,
                    eol='\n')

    def Property(pstr, dtype=float):
        def getter(self):
            return self.get_value(f'{pstr}?', dtype=dtype)

        def setter(self, value):
            value = int(value) if (dtype == bool) else dtype(value)
            self.send(f'{pstr}{value}')
        return pyqtProperty(dtype, getter, setter)

    # Function output controls
    frequency = Property('FREQ')
    invert = Property('INVT', bool)
    offset = Property('OFFS')
    phase = Property('PHSE')
    sampling_frequency = Property('FSMP')
    waveform = Property('FUNC', int)
    # Modulation controls
    modulation = Property('MENA', bool)
    modulation_rate = Property('RATE')
    modulation_type = Property('MTYP', int)
    modulation_waveform = Property('MDWF', int)
    burst_count = Property('BCNT', int)
    am_depth = Property('DPTH', int)
    fm_span = Property('FDEV')
    pm_span = Property('PDEV')
    sweep_span = Property('SPAN')
    sweep_center_frequency = Property('SPCF')
    sweep_start_frequency = Property('STFR')
    sweep_stop_frequency = Property('SPFR')
    trigger_rate = Property('TRAT')
    trigger_source = Property('TSRC', int)

    def __init__(self, portName=None, **kwargs):
        super().__init__(portName, **self.settings, **kwargs)
        self._muted = False

    def identify(self):
        return 'DS345' in self.handshake('*IDN?')

    @pyqtSlot()
    def reset(self):
        '''Rest DS345 to default settings'''
        self.send('*RST')

    @pyqtProperty(float)
    def amplitude(self):
        return float(self.handshake('AMPL?')[:-4])

    @amplitude.setter
    def amplitude(self, value):
        self.send(f'AMPL {value}VP')

    @pyqtProperty(bool)
    def mute(self):
        return self._muted

    @mute.setter
    def mute(self, value):
        if value == self._muted:
            return
        if value:
            self._saved_amplitude = self.amplitude
            self.amplitude = 0.
            self._muted = True
        else:
            self._muted = False
            self.amplitude = self._saved_amplitude

    @pyqtSlot()
    def trigger(self):
        '''Trigger sweep or burst

        Note: Effective if trigger_source=0 (single)
        '''
        if self.trigger_source != 0:
            logger.warn('Only effective if trigger_source is 0.')
        self.send('*TRG')

    def reset_sweep_markers(self):
        self.send('MKSP')

    def set_sweep_span(self):
        self.send('SPMK')

    def set_ttl(self):
        '''Set output to TTL levels'''
        self.send('ATTL')

    def set_ecl(self):
        '''Set output to ECL levels'''
        self.send('AECL')

    def load_waveform(self, waveform):
        '''Load arbitrary waveform

        Arguments
        ---------
        waveform: numpy.array
        '''
        npts = len(waveform)
        if npts > 16300:
            logger.error('waveform can contain at most 16300 points')
            return
        if not self.expect(f'LDWF?0,{npts}', '1'):
            logger.error(f'not able to load waveform of length {npts}.')
            return
        data = np.clip(np.round(waveform), -2048, 2047).astype('>i2')
        checksum = (np.sum(data) & 0xFFFF).astype('>i2')
        data = np.append(data, checksum)
        self.send(data.tobytes())

    def amplitude_modulation(self, waveform):
        '''Load arbitrary amplitude modulation

        Range: -1 (full off) to +1 (full on)
        Maximum length: 10000 points
        '''
        if len(waveform) > 10000:
            logger.error('waveform can contain at most 10000 points')
        signal = np.round(32767.*waveform).astype('>i2')
        checksum = (np.sum(signal) & 0xFFFF).astype('>i2').tobytes()
        self.modulation = False
        self.modulation_type = 2
        self.modulation_waveform = 5
        self.send(f'AMOD?{len(signal)}')
        self.read_until()
        self.send(signal.tobytes())
        self.send(checksum)
        self.modulation = True
