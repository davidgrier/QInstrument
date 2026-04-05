import logging
import numpy as np
from numpy.typing import ArrayLike
from QInstrument.lib.QSerialInstrument import QSerialInstrument


logger = logging.getLogger(__name__)


class QDS345(QSerialInstrument):
    '''SRS DS345 Function Generator

    Properties
    ==========

    Function Output
    ---------------
    amplitude: float [V]
        Peak-to-peak output amplitude.
        Range: 0 <= amplitude <= 5, amplitude + \\|offset\\| <= 5
    frequency: float [Hz]
        Output frequency.
        Range by waveform:

        - sine, square: 1 μHz – 30.2 MHz
        - triangle, ramp: 1 μHz – 100 kHz
        - arbitrary: 2.329 mHz – 40 MHz (sampling rate)
        - noise: 10 MHz (fixed)
    invert: bool
        True: invert output polarity.
    mute: bool
        True: silence output (saves and restores amplitude).
    offset: float [V]
        DC offset voltage.
        Range: -5 <= offset <= 5, amplitude + \\|offset\\| <= 5
    phase: float [degrees]
        Output waveform phase.
        Range: 0.001 – 7199.999
        Note: raises an instrument error if waveform is noise (4)
        or arbitrary (5), or if a sweep or FM is active.
    waveform: int
        Output waveform.
        0: sine, 1: square, 2: triangle, 3: ramp, 4: noise, 5: arbitrary

    Output Modulation
    -----------------
    modulation: bool
        True: enable output modulation.
    modulation_type: int
        0: linear sweep, 1: log sweep, 2: AM, 3: FM, 4: PM, 5: burst
    modulation_waveform: int
        Modulating waveform.
        0: single, 1: ramp, 2: triangle, 3: sine, 4: square,
        5: arbitrary, 6: none (burst mode)
        Note: arbitrary (5) is valid for AM, FM, and PM only, and the
        waveform must be loaded before enabling modulation.
    modulation_rate: float [Hz]
        Modulation rate.
        Range: 0.001 – 10000
    burst_count: int
        Number of cycles per burst.
        Range: 1 – 30000 (burst time must not exceed 500 s)
    am_depth: int [%]
        AM modulation depth.
        Range: 0 – 100. Negative values enable double-sideband
        suppressed-carrier (DSBSC) modulation.
    fm_span: float [Hz]
        Peak frequency deviation for FM.
        Range: 0 – 2 * frequency
    pm_span: float [degrees]
        Peak phase deviation for PM.
        Range: 0 – 7199.999
    sweep_center_frequency: float [Hz]
        Center frequency for frequency sweep.
        Range: 0 – waveform maximum
    sweep_span: float [Hz]
        Span for frequency sweep. Negative values sweep downward.
        Range: \\|sweep_span\\| <= 2 * sweep_center_frequency
    sweep_start_frequency: float [Hz]
        Start frequency for sweep.
        Range: 0 – waveform maximum
    sweep_stop_frequency: float [Hz]
        Stop frequency for sweep.
        Range: 0 – waveform maximum
    trigger_rate: float [Hz]
        Internal trigger rate for bursts and sweeps.
        Range: 0.001 – 10000 (rounded to 2 significant digits)
    trigger_source: int
        Trigger source for bursts and sweeps.
        0: single (see trigger()), 1: internal rate,
        2: external positive slope, 3: external negative slope,
        4: line

    Arbitrary Waveform
    ------------------
    sampling_frequency: float [Hz]
        Sampling rate for arbitrary waveform playback.
        Range: 1 mHz – 40 MHz
    '''

    comm = dict(baudRate=QSerialInstrument.BaudRate.Baud9600,
                dataBits=QSerialInstrument.DataBits.Data8,
                stopBits=QSerialInstrument.StopBits.TwoStop,
                parity=QSerialInstrument.Parity.NoParity,
                flowControl=QSerialInstrument.FlowControl.NoFlowControl,
                eol='\n')

    def __init__(self, portName: str | None = None, **kwargs) -> None:
        super().__init__(portName, **(self.comm | kwargs))
        self._registerProperties()
        self._registerMethods()

    def _registerProperties(self) -> None:
        '''Register all instrument properties via ``registerProperty()``.

        Called once from ``__init__``. Subclasses that extend the property
        set should call ``super()._registerProperties()`` first.
        '''
        self._muted: bool = False
        self._saved_amplitude: float
        register = self.registerProperty
        register('amplitude',
                 getter=lambda: float(self.handshake('AMPL?')[:-4]),
                 setter=lambda v: self.transmit(f'AMPL {float(v)}VP'))
        register('mute', ptype=bool,
                 getter=lambda: self._muted,
                 setter=self._setMute)
        self._register('frequency',              'FREQ')
        self._register('offset',                 'OFFS')
        self._register('phase',                  'PHSE')
        self._register('sampling_frequency',     'FSMP')
        self._register('waveform',               'FUNC', int)
        self._register('invert',                 'INVT', bool)
        self._register('modulation',             'MENA', bool)
        self._register('modulation_type',        'MTYP', int)
        self._register('modulation_waveform',    'MDWF', int)
        self._register('modulation_rate',        'RATE')
        self._register('burst_count',            'BCNT', int)
        self._register('am_depth',               'DPTH', int)
        self._register('fm_span',                'FDEV')
        self._register('pm_span',                'PDEV')
        self._register('sweep_span',             'SPAN')
        self._register('sweep_center_frequency', 'SPCF')
        self._register('sweep_start_frequency',  'STFR')
        self._register('sweep_stop_frequency',   'SPFR')
        self._register('trigger_rate',           'TRAT')
        self._register('trigger_source',         'TSRC', int)

    def _registerMethods(self) -> None:
        '''Register all instrument methods via ``registerMethod()``.

        Called once from ``__init__``. Subclasses that add methods should
        call ``super()._registerMethods()`` first.
        '''
        self.registerMethod('reset', self.reset)
        self.registerMethod('trigger', self.trigger)

    def _register(self, name: str, cmd: str, dtype: type = float) -> None:
        '''Register a standard instrument property.

        Builds getter and setter from the DS345 command convention:
        query is ``cmd + '?'``, set is ``cmd + value``. Bool properties
        are transmitted as integers (0/1) per the instrument protocol.

        Parameters
        ----------
        name : str
            Property name passed to ``registerProperty``.
        cmd : str
            DS345 command mnemonic (e.g. ``'FREQ'``).
        dtype : type, optional
            Value type: ``float`` (default), ``int``, or ``bool``.
        '''
        if dtype is bool:
            def getter(): return bool(self.getValue(f'{cmd}?', int))
            def setter(v): return self.transmit(f'{cmd}{int(bool(v))}')
        else:
            def getter(): return self.getValue(f'{cmd}?', dtype)
            def setter(v): return self.transmit(f'{cmd}{dtype(v)}')
        self.registerProperty(name, getter=getter, setter=setter, ptype=dtype)

    def identify(self) -> bool:
        '''Return True if the connected device identifies as a DS345.

        Queries the instrument identification string (``*IDN?``) and
        checks for the ``'DS345'`` model token in the response.
        '''
        return 'DS345' in self.handshake('*IDN?')

    def reset(self) -> None:
        '''Reset the DS345 to its factory default settings.'''
        self.transmit('*RST')

    def trigger(self) -> None:
        '''Issue a single trigger for a burst or sweep.

        Only effective when ``trigger_source`` is 0 (single trigger
        mode). Logs a warning otherwise.
        '''
        if self.getValue('TSRC?', int) != 0:
            logger.warning(
                'trigger() is only effective when trigger_source is 0.')
        self.transmit('*TRG')

    def _setMute(self, value: bool) -> None:
        '''Setter for the ``mute`` property.

        On mute: reads and saves the current amplitude, then sets it
        to zero. On unmute: restores the saved amplitude. Idempotent —
        repeated calls with the same value are no-ops.
        '''
        value = bool(value)
        if value == self._muted:
            return
        if value:
            amplitude = self.get('amplitude')
            assert amplitude is not None
            self._saved_amplitude = float(amplitude)
            self.transmit('AMPL 0.0VP')
            self._muted = True
        else:
            self._muted = False
            self.transmit(f'AMPL {self._saved_amplitude}VP')

    def set_span_from_markers(self) -> None:
        '''Set the sweep span from the current marker positions (MKSP).'''
        self.transmit('MKSP')

    def set_markers_from_span(self) -> None:
        '''Set the marker positions from the current sweep span (SPMK).'''
        self.transmit('SPMK')

    def set_ttl(self) -> None:
        '''Set output amplitude and offset to TTL levels.'''
        self.transmit('ATTL')

    def set_ecl(self) -> None:
        '''Set output amplitude and offset to ECL levels.'''
        self.transmit('AECL')

    def load_waveform(self, waveform: ArrayLike) -> None:
        '''Load an arbitrary waveform into the DS345.

        Parameters
        ----------
        waveform : ArrayLike
            Up to 16300 samples. Values are clipped and rounded to
            the range [-2048, 2047] before transmission.
        '''
        data = np.asarray(waveform)
        npts = len(data)
        if npts > 16300:
            logger.error('waveform can contain at most 16300 points')
            return
        if not self.expect(f'LDWF?0,{npts}', '1'):
            logger.error(f'Not able to load waveform of length {npts}.')
            return
        data = np.clip(np.round(data), -2048, 2047).astype('>i2')
        checksum = (np.sum(data) & 0xFFFF).astype('>i2')
        data = np.append(data, checksum)
        self.transmit(data.tobytes())

    def amplitude_modulation(self, waveform: ArrayLike) -> None:
        '''Load an arbitrary amplitude modulation waveform.

        Configures the instrument for arbitrary AM and uploads the
        waveform. Modulation is enabled on completion.

        Parameters
        ----------
        waveform : ArrayLike
            Up to 10000 samples normalized to [-1, 1], where -1 is
            full off and +1 is full on.
        '''
        data = np.asarray(waveform)
        if len(data) > 10000:
            logger.error('waveform can contain at most 10000 points')
            return
        signal = np.round(32767. * data).astype('>i2')
        checksum = (np.sum(signal) & 0xFFFF).astype('>i2').tobytes()
        self.transmit('MENA0')
        self.transmit('MTYP2')
        self.transmit('MDWF5')
        self.transmit(f'AMOD?{len(signal)}')
        self.receive()
        self.transmit(signal.tobytes())
        self.transmit(checksum)
        self.transmit('MENA1')


if __name__ == '__main__':
    QDS345.example()

__all__ = ['QDS345']
