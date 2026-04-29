import logging
from qtpy import QtCore
from QInstrument.lib.QPollingMixin import QPollingMixin
from QInstrument.lib.QSerialInstrument import QSerialInstrument


logger = logging.getLogger(__name__)


class QSR844(QPollingMixin, QSerialInstrument):
    '''SRS SR844 RF Lock-in Amplifier

    Properties
    ==========

    Reference and Phase
    -------------------
    frequency : float [Hz]
        Reference frequency for the internal oscillator.
        Rounded to 5 significant digits or 0.0001 Hz, whichever is greater.
        Range: 25 MHz <= frequency <= 200 MHz
    harmonic : int
        Detection harmonic.
        Range: 1 <= harmonic < 20000, frequency * harmonic <= 200 MHz
    internal_reference : bool
        True: use internal reference source.
        False: use external reference source.
    phase : float [degrees]
        Reference phase shift.
        Range: -360 <= phase <= 729.99
    reference_impedance : int
        Reference input impedance.
        0: 50 Ohm, 1: 10 kOhm

    Signal Input
    ------------
    input_impedance : int
        Signal input impedance.
        0: 50 Ohm, 1: 1 MOhm
    wide_reserve : int
        Wide-band dynamic reserve mode.
        0: high reserve, 1: normal, 2: low noise

    Gain and Time Constant
    ----------------------
    close_reserve : int
        Close-in dynamic reserve mode.
        0: high reserve, 1: normal, 2: low noise
    low_pass_slope : int
        0: 6 dB/octave, 1: 12 dB/octave, 2: 18 dB/octave, 3: 24 dB/octave
    sensitivity : int
        0: 100 nVrms / -127 dBm    8:   1 mVrms /  -47 dBm
        1: 300 nVrms / -117 dBm    9:   3 mVrms /  -37 dBm
        2:   1 μVrms / -107 dBm   10:  10 mVrms /  -27 dBm
        3:   3 μVrms /  -97 dBm   11:  30 mVrms /  -17 dBm
        4:  10 μVrms /  -87 dBm   12: 100 mVrms /   -7 dBm
        5:  30 μVrms /  -77 dBm   13: 300 mVrms /   +3 dBm
        6: 100 μVrms /  -67 dBm   14:   1  Vrms /  +13 dBm
        7: 300 μVrms /  -57 dBm
    time_constant : int
        Input filter time constant.
        0: 100 μs     9:   3 s
        1: 300 μs    10:  10 s
        2:   1 ms    11:  30 s
        3:   3 ms    12: 100 s
        4:  10 ms    13: 300 s
        5:  30 ms    14:   1 ks
        6: 100 ms    15:   3 ks
        7: 300 ms    16:  10 ks
        8:   1 s     17:  30 ks

    Output (read-only)
    ------------------
    reference_frequency : int [Hz]
        Actual reference frequency being used.
    if_frequency : int [Hz]
        IF frequency (reference frequency mod 200 MHz).
    x : float [V]
        In-phase (X) component of the lock-in signal.
    y : float [V]
        Quadrature (Y) component of the lock-in signal.
    r : float [V]
        Magnitude R of the lock-in signal.
    theta : float [degrees]
        Phase angle theta of the lock-in signal.
    '''

    comm = dict(baudRate=QSerialInstrument.BaudRate.Baud19200,
                dataBits=QSerialInstrument.DataBits.Data8,
                stopBits=QSerialInstrument.StopBits.OneStop,
                parity=QSerialInstrument.Parity.NoParity,
                flowControl=QSerialInstrument.FlowControl.NoFlowControl,
                eol='\r')

    def _registerProperties(self) -> None:
        '''Register all instrument properties via ``registerProperty()``.

        Called automatically by ``QAbstractInstrument.__init__``. Subclasses
        that extend the property set should call
        ``super()._registerProperties()`` first.
        '''
        # Reference and Phase
        self._register('frequency',           'FREQ', float)
        self._register('harmonic',            'HARM', int)
        self._register('internal_reference',  'FMOD', bool)
        self._register('phase',               'PHAS', float)
        self._register('reference_impedance', 'REFZ', int)
        # Signal Input
        self._register('input_impedance', 'INPZ', int)
        self._register('wide_reserve',    'WRSV', int)
        # Gain and Time Constant
        self._register('close_reserve',  'CRSV', int)
        self._register('low_pass_slope', 'OFSL', int)
        self._register('sensitivity',    'SENS', int)
        self._register('time_constant',  'OFLT', int)
        # Read-only frequency displays
        self.registerProperty('reference_frequency', setter=None, ptype=int,
                              getter=lambda: self.getValue('FRAQ?', int))
        self.registerProperty('if_frequency', setter=None, ptype=int,
                              getter=lambda: self.getValue('FRIQ?', int))
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

        Called automatically by ``QAbstractInstrument.__init__``. Subclasses
        that add methods should call ``super()._registerMethods()`` first.
        '''
        self.registerMethod('reset',              self.reset)
        self.registerMethod('auto_gain',          self.auto_gain)
        self.registerMethod('auto_close_reserve', self.auto_close_reserve)
        self.registerMethod('auto_wide_reserve',  self.auto_wide_reserve)
        self.registerMethod('auto_phase',         self.auto_phase)
        self.registerMethod('auto_offset_x',      self.auto_offset_x)
        self.registerMethod('auto_offset_y',      self.auto_offset_y)
        self.registerMethod('auto_offset_r',      self.auto_offset_r)

    def _register(self, name: str, cmd: str, dtype: type = float) -> None:
        '''Register a standard instrument property.

        Builds getter and setter from the SR844 command convention:
        query is ``cmd + '?'``, set is ``cmd + value``. Bool properties
        are transmitted as integers (0/1) per the instrument protocol.

        Parameters
        ----------
        name : str
            Property name passed to ``registerProperty``.
        cmd : str
            SR844 command mnemonic (e.g. ``'FREQ'``).
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
        '''Return True if the connected device identifies as an SR844.

        Queries the instrument identification string (``*IDN?``) and
        checks for the ``'SR844'`` model token in the response.
        '''
        return 'SR844' in self.handshake('*IDN?')

    def _poll(self) -> None:
        '''Poll frequency, R, and theta simultaneously and emit results.

        Overrides :meth:`QPollingMixin._poll` to use the ``SNAP?9,3,4``
        batch command instead of three sequential queries, keeping the
        captured values time-coherent.
        '''
        if not getattr(self, '_polling', False):
            return
        frequency, r, theta = self.report()
        self.propertyValue.emit('frequency', frequency)
        self.propertyValue.emit('r', r)
        self.propertyValue.emit('theta', theta)
        if getattr(self, '_polling', False):
            QtCore.QTimer.singleShot(
                self.POLL_INTERVAL, self._poll)

    def report(self) -> list[float]:
        '''Return the current frequency, magnitude, and phase simultaneously.

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
        '''Reset the SR844 to its factory default settings.'''
        self.transmit('*RST')

    def auto_gain(self) -> None:
        '''Automatically adjust the sensitivity (autorange gain).'''
        self.transmit('AGAN')

    def auto_close_reserve(self) -> None:
        '''Automatically adjust the close-in dynamic reserve.'''
        self.transmit('ACRS')

    def auto_wide_reserve(self) -> None:
        '''Automatically adjust the wide-band dynamic reserve.'''
        self.transmit('AWRS')

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

        Parameters
        ----------
        channel : int
            1: X, 2: Y, 3: R
        '''
        if channel not in (1, 2, 3):
            logger.warning(f'auto_offset: channel must be 1, 2, or 3 (got {channel})')
            return
        self.transmit(f'AOFF{channel}')


if __name__ == '__main__':
    QSR844.example()

__all__ = ['QSR844']
