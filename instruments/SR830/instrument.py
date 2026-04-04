import logging
from QInstrument.lib.QSerialInstrument import QSerialInstrument


logger = logging.getLogger(__name__)


class QSR830(QSerialInstrument):
    '''SRS SR830 Lock-in Amplifier

    Properties
    ==========

    Reference and Phase
    -------------------
    amplitude : float [V]
        Amplitude of the reference sine output.
        Rounded to 0.002 V.
        Range: 0.004 <= amplitude <= 5.000
    frequency : float [Hz]
        Reference frequency for the internal oscillator.
        Rounded to 5 significant digits or 0.0001 Hz, whichever is greater.
        Range: 0.001 <= frequency, frequency * harmonic <= 102000
    harmonic : int
        Detection harmonic.
        Range: 1 <= harmonic < 20000, frequency * harmonic <= 102000
    internal_reference : bool
        True: use internal reference source.
        False: use external reference source.
    phase : float [degrees]
        Reference phase shift.
        Range: -360 <= phase <= 729.99
    reference_trigger : int
        Reference trigger for external reference.
        0: sine zero crossing, 1: TTL rising edge, 2: TTL falling edge.
        Must be 1 or 2 when frequency < 1 Hz.

    Input and Filter
    ----------------
    dc_coupling : bool
        True: DC-coupled inputs.
        False: AC-coupled inputs.
    input_configuration : int
        0: channel A, 1: A - B, 2: I (1 MOhm), 3: I (100 MOhm)
    line_filter : int
        Input line notch filter configuration.
        0: no filters, 1: line notch, 2: 2x line notch, 3: both notch filters
    shield_grounding : bool
        True: input shielding is grounded.
        False: input shielding is floating.

    Gain and Time Constant
    ----------------------
    dynamic_reserve : int
        0: high dynamic reserve, 1: normal, 2: low noise
    low_pass_slope : int
        0: 6 dB/octave, 1: 12 dB/octave, 2: 18 dB/octave, 3: 24 dB/octave
    sensitivity : int
        0:   2 nV/fA    10:   5 uV/pA    20:  10 mV/nA
        1:   5 nV/fA    11:  10 uV/pA    21:  20 mV/nA
        2:  10 nV/fA    12:  20 uV/pA    22:  50 mV/nA
        3:  20 nV/fA    13:  50 uV/pA    23: 100 mV/nA
        4:  50 nV/fA    14: 100 uV/pA    24: 200 mV/nA
        5: 100 nV/fA    15: 200 uV/pA    25: 500 mV/nA
        6: 200 nV/fA    16: 500 uV/pA    26:   1  V/uA
        7: 500 nV/fA    17:   1 mV/nA
        8:   1 uV/pA    18:   2 mV/nA
        9:   2 uV/pA    19:   5 mV/nA
    synchronous_filter : bool
        True: synchronous filtering below 200 Hz
        (only engaged when harmonic * frequency < 200 Hz).
        False: no synchronous filter.
    time_constant : int
        Input filter time constant.
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
    '''

    comm = dict(baudRate=QSerialInstrument.BaudRate.Baud9600,
                dataBits=QSerialInstrument.DataBits.Data8,
                stopBits=QSerialInstrument.StopBits.OneStop,
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
        # Reference and Phase
        self._register('amplitude',          'SLVL', float)
        self._register('frequency',          'FREQ', float)
        self._register('harmonic',           'HARM', int)
        self._register('internal_reference', 'FMOD', bool)
        self._register('phase',              'PHAS', float)
        self._register('reference_trigger',  'RSLP', int)
        # Input and Filter
        self._register('dc_coupling',          'ICPL', bool)
        self._register('input_configuration',  'ISRC', int)
        self._register('line_filter',          'ILIN', int)
        self._register('shield_grounding',     'IGND', bool)
        # Gain and Time Constant
        self._register('dynamic_reserve',    'RMOD', int)
        self._register('low_pass_slope',     'OFSL', int)
        self._register('sensitivity',        'SENS', int)
        self._register('synchronous_filter', 'SYNC', bool)
        self._register('time_constant',      'OFLT', int)

    def _registerMethods(self) -> None:
        '''Register all instrument methods via ``registerMethod()``.

        Called once from ``__init__``. Subclasses that add methods should
        call ``super()._registerMethods()`` first.
        '''
        self.registerMethod('reset',        self.reset)
        self.registerMethod('auto_gain',    self.auto_gain)
        self.registerMethod('auto_reserve', self.auto_reserve)
        self.registerMethod('auto_phase',   self.auto_phase)

    def _register(self, name: str, cmd: str, dtype: type = float) -> None:
        '''Register a standard instrument property.

        Builds getter and setter from the SR830 command convention:
        query is ``cmd + '?'``, set is ``cmd + value``. Bool properties
        are transmitted as integers (0/1) per the instrument protocol.

        Parameters
        ----------
        name : str
            Property name passed to ``registerProperty``.
        cmd : str
            SR830 command mnemonic (e.g. ``'FREQ'``).
        dtype : type, optional
            Value type: ``float`` (default), ``int``, or ``bool``.
        '''
        if dtype is bool:
            def getter(): return bool(self.getValue(f'{cmd}?', int))
            def setter(v): self.transmit(f'{cmd}{int(bool(v))}')
        else:
            def getter(): return self.getValue(f'{cmd}?', dtype)
            def setter(v): self.transmit(f'{cmd}{dtype(v)}')
        self.registerProperty(name, getter=getter, setter=setter, ptype=dtype)

    def identify(self) -> bool:
        '''Return True if the connected device identifies as an SR830.

        Queries the instrument identification string (``*IDN?``) and
        checks for the ``'SR830'`` model token in the response.
        '''
        return 'SR830' in self.handshake('*IDN?')

    def report(self) -> list[float]:
        '''Return the current frequency, magnitude, and phase.

        Queries the instrument using the SNAP command for simultaneous
        capture of frequency (9), R (3), and theta (4).

        Returns
        -------
        list[float]
            [frequency [Hz], R [V], theta [degrees]]
        '''
        response = self.handshake('SNAP?9,3,4')
        return list(map(float, response.split(',')))

    def reset(self) -> None:
        '''Reset the SR830 to its factory default settings.'''
        self.transmit('*RST')

    def auto_gain(self) -> None:
        '''Automatically adjust the sensitivity (autorange gain).'''
        self.transmit('AGAN')

    def auto_reserve(self) -> None:
        '''Automatically adjust the dynamic reserve.'''
        self.transmit('ARSV')

    def auto_phase(self) -> None:
        '''Automatically adjust the reference phase.'''
        self.transmit('APHS')

    def auto_offset(self, channel: int) -> None:
        '''Automatically offset the specified output channel to zero.

        Parameters
        ----------
        channel : int
            1: X, 2: Y, 3: R
        '''
        self.transmit(f'AOFF{channel}')


if __name__ == '__main__':
    QSR830.example()

__all__ = ['QSR830']
