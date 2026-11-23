from typing import ClassVar
import numpy as np
from QInstrument.lib.QSerialInstrument import QSerialInstrument


class QTDS1000(QSerialInstrument):
    '''Tektronix TDS1000-series digital oscilloscope: waveform acquisition.

    Experimental.  This class reads waveforms; it registers no properties,
    so it has no widget, tree or fake.  A waveform is read in the binary
    ``RPB`` encoding, one byte per sample, and converted to volts with the
    scale factors that the oscilloscope reports.

    Methods
    =======
    data(channel)
        Acquire the waveform on a channel: ``(t, v)`` arrays.
    '''

    comm: ClassVar[dict] = dict(baudRate=QSerialInstrument.BaudRate.Baud9600,
                dataBits=QSerialInstrument.DataBits.Data8,
                stopBits=QSerialInstrument.StopBits.OneStop,
                parity=QSerialInstrument.Parity.NoParity,
                flowControl=QSerialInstrument.FlowControl.HardwareControl,
                eol=b'\n',
                timeout=500)

    def __init__(self, portName: str | None = None, **kwargs) -> None:
        super().__init__(portName, **(self.comm | kwargs))

    def identify(self) -> bool:
        '''Return True if the device answers ``*IDN?`` as a Tektronix.

        Checks the response for the string ``'TEKTRONIX'``.
        '''
        return 'TEKTRONIX' in self.handshake('*IDN?')

    def _number(self, query: str) -> float:
        '''Query a numeric setting of the oscilloscope.

        Parameters
        ----------
        query : str
            Query command (for example ``'WFMPRE:YMULT?'``).

        Returns
        -------
        float
            The value that the oscilloscope reports.

        Raises
        ------
        ValueError
            If the response is not a number.
        '''
        value = self.getValue(query)
        if value is None:
            raise ValueError(f'No numeric response to {query}')
        return float(value)

    def _readBlock(self) -> bytes:
        '''Read an IEEE 488.2 definite-length binary block.

        The block is ``#<n><length><data>`` followed by a terminator, where
        ``<n>`` is a single digit giving the number of digits of
        ``<length>``.  It is read by its declared length, not by looking for
        the end-of-line character: a sample may have the value of one.

        Returns
        -------
        bytes
            The data of the block.

        Raises
        ------
        ValueError
            If the response does not begin a block.
        TimeoutError
            If the block is shorter than it declares.
        '''
        header = self.readn(2)
        if len(header) < 2 or header[:1] != b'#' or not header[1:].isdigit():
            raise ValueError(f'Not a binary block: {header!r}')
        digits = self.readn(int(header[1:]))
        length = int(digits)
        data = self.readn(length)
        if len(data) < length:
            raise TimeoutError(
                f'Received {len(data)} of {length} bytes of the waveform')
        self.readn(1)                      # the terminator
        return data

    def data(self, channel: str = 'CH1') -> tuple[np.ndarray, np.ndarray]:
        '''Acquire the waveform on a channel.

        Asks for the waveform in one-byte ``RPB`` encoding and converts
        it with the scale factors of the oscilloscope.  The time axis is
        centered on the horizontal position.

        Parameters
        ----------
        channel : str
            Source of the waveform: ``'CH1'``, ``'CH2'``, ``'MATH'`` ...
            Default: ``'CH1'``.

        Returns
        -------
        t : numpy.ndarray
            Time of each sample [s].
        v : numpy.ndarray
            Value of each sample [V].

        Raises
        ------
        ValueError
            If the oscilloscope does not answer with a binary block or a
            scale factor.
        TimeoutError
            If the waveform is incomplete.
        '''
        self.transmit(f'DATA:SOURCE {channel}')
        self.transmit('DATA:WIDTH 1')
        self.transmit('DATA:ENC RPB')
        adc0 = self._number('WFMPRE:YOFF?')
        dx = self._number('WFMPRE:XINCR?')
        x0 = self._number('HOR:POS?')
        scale = self._number('WFMPRE:YMULT?')
        y0 = self._number('WFMPRE:YZERO?')
        self.transmit('CURVE?')
        adc = np.frombuffer(self._readBlock(), dtype=np.uint8)
        t = (np.arange(adc.size) - adc.size / 2.) * dx + x0
        v = scale * (adc - adc0) + y0
        return t, v


def example() -> None:
    '''Acquire CH1, plot it, and save it to ``tds1000.csv``.'''
    import matplotlib.pyplot as plt  # pyright: ignore[reportMissingImports]
    from qtpy.QtCore import QCoreApplication

    if QCoreApplication.instance() is None:
        QCoreApplication([])
    scope = QTDS1000().find()
    if not scope.isOpen():
        print('QTDS1000: oscilloscope not found.')
        return
    t, v = scope.data('CH1')
    plt.plot(t, v)
    plt.xlabel('time [s]')
    plt.ylabel('signal [V]')
    plt.show()
    np.savetxt('tds1000.csv', np.vstack([t, v]), delimiter=',')


if __name__ == '__main__':
    example()

__all__ = ['QTDS1000']
