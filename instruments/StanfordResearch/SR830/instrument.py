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
        Range: 0.001 Hz <= frequency, frequency * harmonic <= 102 kHz
    harmonic : int
        Detection harmonic.
        Range: 1 <= harmonic < 20000, frequency * harmonic <= 102 kHz
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
        Voltage input sensitivities (V/V mode):
        0:   2 nV/fA    10:   5 μV/pA    20:  10 mV/nA
        1:   5 nV/fA    11:  10 μV/pA    21:  20 mV/nA
        2:  10 nV/fA    12:  20 μV/pA    22:  50 mV/nA
        3:  20 nV/fA    13:  50 μV/pA    23: 100 mV/nA
        4:  50 nV/fA    14: 100 μV/pA    24: 200 mV/nA
        5: 100 nV/fA    15: 200 μV/pA    25: 500 mV/nA
        6: 200 nV/fA    16: 500 μV/pA    26:   1  V/μA
        7: 500 nV/fA    17:   1 mV/nA
        8:   1 μV/pA    18:   2 mV/nA
        9:   2 μV/pA    19:   5 mV/nA
    synchronous_filter : bool
        True: synchronous filtering below 200 Hz
        (only engaged when harmonic * frequency < 200 Hz).
        False: no synchronous filter.
    time_constant : int
        Input filter time constant.
        0:  20 μs    10:   1 s
        1:  30 μs    11:   3 s
        2: 100 μs    12:  10 s
        3: 300 μs    13:  30 s
        4:   1 ms    14: 100 s
        5:   3 ms    15: 300 s
        6:  10 ms    16:   1 ks
        7:  30 ms    17:   3 ks
        8: 100 ms    18:  10 ks
        9: 300 ms    19:  30 ks

    Output (read-only)
    ------------------
    x : float [V]
        In-phase (X) component of the lock-in signal.
    y : float [V]
        Quadrature (Y) component of the lock-in signal.
    r : float [V]
        Magnitude R of the lock-in signal.
    theta : float [degrees]
        Phase angle theta of the lock-in signal.
    '''

    comm = dict(baudRate=QSerialInstrument.BaudRate.Baud9600,
                dataBits=QSerialInstrument.DataBits.Data8,
                stopBits=QSerialInstrument.StopBits.OneStop,
                parity=QSerialInstrument.Parity.NoParity,
                flowControl=QSerialInstrument.FlowControl.NoFlowControl,
                eol='\n')

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
        self._register('dc_coupling',         'ICPL', bool)
        self._register('input_configuration', 'ISRC', int)
        self._register('line_filter',         'ILIN', int)
        self._register('shield_grounding',    'IGND', bool)
        # Gain and Time Constant
        self._register('dynamic_reserve',    'RMOD', int)
        self._register('low_pass_slope',     'OFSL', int)
        self._register('sensitivity',        'SENS', int)
        self._register('synchronous_filter', 'SYNC', bool)
        self._register('time_constant',      'OFLT', int)
        # Output channels (read-only)
        self.registerProperty('x', setter=None, ptype=float,
                              getter=lambda: self.getValue('OUTP?1', float))
        self.registerProperty('y', setter=None, ptype=float,
                              getter=lambda: self.getValue('OUTP?2', float))
        self.registerProperty('r', setter=None, ptype=float,
                              getter=lambda: self.getValue('OUTP?3', float))
        self.registerProperty('theta', setter=None, ptype=float,
                              getter=lambda: self.getValue('OUTP?4', float))

    def _registerMethods(self) -> None:
        '''Register all instrument methods via ``registerMethod()``.

        Called once from ``__init__``. Subclasses that add methods should
        call ``super()._registerMethods()`` first.
        '''
        self.registerMethod('reset',          self.reset)
        self.registerMethod('auto_gain',      self.auto_gain)
        self.registerMethod('auto_reserve',   self.auto_reserve)
        self.registerMethod('auto_phase',     self.auto_phase)
        self.registerMethod('auto_offset_x',  self.auto_offset_x)
        self.registerMethod('auto_offset_y',  self.auto_offset_y)
        self.registerMethod('auto_offset_r',  self.auto_offset_r)

    def _register(self, name: str, cmd: str, ptype: type = float) -> None:
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
        ptype : type, optional
            Value type: ``float`` (default), ``int``, or ``bool``.
        '''
        if ptype is bool:
            def getter(): return bool(self.getValue(f'{cmd}?', int))
            def setter(v): self.transmit(f'{cmd}{int(bool(v))}')
        else:
            def getter(): return self.getValue(f'{cmd}?', ptype)
            def setter(v): self.transmit(f'{cmd}{ptype(v)}')
        self.registerProperty(name, getter=getter, setter=setter,
                              ptype=ptype)

    def identify(self) -> bool:
        '''Return True if the connected device identifies as an SR830.

        Queries the instrument identification string (``*IDN?``) and
        checks for the ``'SR830'`` model token in the response.
        '''
        return 'SR830' in self.handshake('*IDN?')

    def report(self) -> list[float]:
        '''Return the current frequency, magnitude, and phase.

        Uses the SNAP command for simultaneous capture, avoiding the
        timing errors that would result from three sequential queries.

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

    def auto_offset_x(self) -> None:
        '''Automatically offset the X output channel to zero.'''
        self.auto_offset(1)

    def auto_offset_y(self) -> None:
        '''Automatically offset the Y output channel to zero.'''
        self.auto_offset(2)

    def auto_offset_r(self) -> None:
        '''Automatically offset the R output channel to zero.'''
        self.auto_offset(3)

    def auto_offset(self, channel: int) -> None:
        '''Automatically offset the specified output channel to zero.

        Prefer the dedicated methods :meth:`auto_offset_x`,
        :meth:`auto_offset_y`, and :meth:`auto_offset_r` for widget binding.

        Parameters
        ----------
        channel : int
            1: X, 2: Y, 3: R
        '''
        if channel not in (1, 2, 3):
            logger.warning(
                f'auto_offset: channel must be 1, 2, or 3 (got {channel})')
            return
        self.transmit(f'AOFF{channel}')


if __name__ == '__main__':
    QSR830.example()

__all__ = ['QSR830']
