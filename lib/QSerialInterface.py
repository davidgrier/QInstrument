import logging

from qtpy import QtCore
from qtpy.QtSerialPort import QSerialPort, QSerialPortInfo


logger = logging.getLogger(__name__)


class QSerialInterface(QSerialPort):
    '''Base class for instruments connected to serial ports.

    Wraps ``QSerialPort`` to provide instrument-oriented communication:
    automatic port discovery via :meth:`find`, custom end-of-line handling
    for :meth:`transmit` and :meth:`receive`, and optional non-blocking
    (signal-driven) I/O.

    Parameters
    ----------
    portName : str | None
        Name of the serial port to open on construction, without the
        system-dependent path prefix (e.g. ``'ttyUSB0'``, ``'COM1'``).
        If ``None``, no port is opened.
    eol : bytes | str
        End-of-line sequence appended to outgoing strings by
        :meth:`transmit` and used as the read terminator by
        :meth:`receive`. Default: ``''`` (no terminator).
    timeout : int
        Milliseconds to wait for incoming data before giving up.
        Default: ``100``.
    blocking : bool
        If ``True`` (default), I/O is synchronous (polling).
        If ``False``, incoming data is handled by the
        :attr:`dataReady` signal.

    Attributes
    ----------
    eol : bytes
        End-of-line sequence used for read/write termination.
    timeout : int
        Read timeout in milliseconds.
    blocking : bool
        Toggles between synchronous polling and signal-driven I/O.

    Signals
    -------
    dataReady(str)
        Emitted in non-blocking mode when a complete line (terminated
        by :attr:`eol`) has been received.

    Examples
    --------
    Synchronous use with automatic port discovery:

    >>> instrument = QSerialInterface(eol='\\n').find()

    Non-blocking use with a signal handler:

    >>> instrument = QSerialInterface(eol='\\n', blocking=False)
    >>> instrument.dataReady.connect(handle_response)
    >>> instrument = instrument.find()
    '''

    dataReady = QtCore.Signal(str)

    def __init__(self,
                 portName: str = '',
                 eol: bytes | str = '',
                 timeout: int | None = None,
                 blocking: bool = True,
                 baudRate=None,
                 dataBits=None,
                 stopBits=None,
                 parity=None,
                 flowControl=None,
                 **kwargs) -> None:
        super().__init__(**kwargs)
        if baudRate is not None:
            self.setBaudRate(baudRate)
        if dataBits is not None:
            self.setDataBits(dataBits)
        if stopBits is not None:
            self.setStopBits(stopBits)
        if parity is not None:
            self.setParity(parity)
        if flowControl is not None:
            self.setFlowControl(flowControl)
        self.eol = eol if isinstance(eol, bytes) else eol.encode()
        self.timeout = timeout or 100
        self.blocking = blocking
        self._buffer = QtCore.QByteArray()
        self.open(portName)

    def identify(self, **kwargs) -> bool:
        '''Verify that the connected device is the expected instrument.

        The base implementation always returns ``True``. Subclasses should
        override this method to query the device and confirm its identity.

        Returns
        -------
        bool
            ``True`` if the device is recognized, ``False`` otherwise.
        '''
        return True

    def open(self, portName: str, **kwargs) -> bool:
        '''Open serial communication with the instrument.

        Opens the specified port in read/write mode and calls
        :meth:`identify` to confirm the correct device is connected.
        The port is closed again if identification fails.

        Parameters
        ----------
        portName : str
            Name of the serial port device file, without the
            system-dependent path prefix.
            Examples: ``'ttyUSB0'``, ``'COM1'``.
        **kwargs
            Passed through to :meth:`identify`.

        Returns
        -------
        bool
            ``True`` if the port was opened and the device identified
            successfully.
        '''
        if len(portName) == 0:
            return False
        self.setPortName(portName)
        if super().open(QSerialPort.OpenModeFlag.ReadWrite):
            self.clear()
            if not self.identify(**kwargs):
                logger.warning(f'Device on {portName} '
                               f'is not {self.__class__.__name__}')
                self.close()
        else:
            logger.warning(f'Could not open {portName}')
        return self.isOpen()

    def find(self, **kwargs) -> 'QSerialInterface':
        '''Poll all available serial ports to locate the instrument.

        Calls :meth:`open` on each port returned by
        ``QSerialPortInfo.availablePorts()`` until one succeeds or all
        ports are exhausted.

        Parameters
        ----------
        **kwargs
            Passed through to :meth:`identify`.

        Returns
        -------
        QSerialInterface
            The instance itself, whether or not a device was found.
            Call :meth:`isOpen` to check the result.
        '''
        for port in QSerialPortInfo.availablePorts():
            portName = port.portName()
            logger.debug(f'Trying to open {portName}')
            if self.open(portName, **kwargs):
                break
        else:
            className = self.__class__.__name__
            logger.error(f'Could not find {className}')
        return self

    @property
    def blocking(self) -> bool:
        '''bool: If ``True``, I/O is synchronous;
           if ``False``, signal-driven.
        '''
        return self._blocking

    @blocking.setter
    def blocking(self, blocking: bool) -> None:
        if blocking:
            try:
                self.readyRead.disconnect(self._handleReadyRead)
            except TypeError:
                pass
        else:
            self.readyRead.connect(self._handleReadyRead)
        self._blocking = blocking

    def transmit(self, data: str | bytes) -> None:
        '''Transmit data to the instrument.

        Strings are encoded to bytes and appended with :attr:`eol` before
        transmission. Raw ``bytes`` are written as-is without appending
        :attr:`eol`.

        Parameters
        ----------
        data : str | bytes
            Data to transmit. Pass a ``str`` for normal ASCII commands;
            pass ``bytes`` for binary payloads that must not be modified.
        '''
        if not self.isOpen():
            logger.warning('Cannot send data: device is not open.')
            return
        if isinstance(data, str):
            data = data.encode() + self.eol
        self.write(data)
        self.flush()
        logger.debug(f'sent: {data}')

    def receive(self,
                eol: str | bytes | None = None,
                raw: bool = False) -> str | bytes:
        '''Read from the serial interface until the end-of-line sequence.

        Reads available data into a buffer until :attr:`eol` is found or
        the read times out. The EOL bytes are stripped from the returned
        value.

        Parameters
        ----------
        eol : str | bytes | None
            End-of-line sequence to match. Defaults to the instance
            :attr:`eol` attribute.
        raw : bool
            If ``True``, return the response as ``bytes``.
            If ``False``, decode and return as ``str``.
            Default: ``False``.

        Returns
        -------
        str | bytes
            Data received from the instrument, with the EOL sequence
            stripped. Returns an empty value on timeout.
        '''
        if eol is not None:
            eol = eol.encode() if isinstance(eol, str) else eol
        else:
            eol = self.eol
        buffer = b''
        while True:
            if (not self.bytesAvailable() and
                    not self.waitForReadyRead(self.timeout)):
                logger.warning('Timeout waiting for response')
                break
            buffer += bytes(self.readAll())
            if eol and eol in buffer:
                buffer = buffer[:buffer.index(eol)]
                break
        return buffer if raw else buffer.decode()

    def readn(self, n: int = 1) -> bytes:
        '''Receive exactly n bytes from the instrument.

        Parameters
        ----------
        n : int
            Number of bytes to read. Default: ``1``.

        Returns
        -------
        bytes
            Data received from the instrument. May be shorter than ``n``
            if the read times out.
        '''
        if not self.isOpen():
            logger.warning('Cannot read data: device is not open.')
            return b''
        buffer = b''
        while len(buffer) < n:
            if (not self.bytesAvailable() and
                    not self.waitForReadyRead(self.timeout)):
                logger.warning('Timeout waiting for response')
                break
            buffer += bytes(self.readAll())
        return buffer[:n]

    def sendbreak(self, duration: int = 250) -> None:
        '''Send a break signal to the instrument.

        Parameters
        ----------
        duration : int
            Duration of the break state in milliseconds.
            Valid range: [1, 500]. Default: ``250``.
        '''
        if not self.isOpen():
            logger.warning('Cannot send break: port is not open.')
            return
        self.setBreakEnabled(True)
        QtCore.QTimer.singleShot(duration, lambda: self.setBreakEnabled(False))

    @QtCore.Slot()
    def _handleReadyRead(self) -> None:
        '''Slot for non-blocking data reception.

        Accumulates incoming bytes in an internal buffer. When a complete
        line (terminated by :attr:`eol`) is detected, emits
        :attr:`dataReady` with the decoded string.
        '''
        self._buffer.append(self.readAll())
        if self._buffer.contains(self.eol):
            pos = self._buffer.indexOf(self.eol)
            eol_end = pos + len(self.eol)
            data = bytes(self._buffer.left(pos))
            if eol_end < self._buffer.size():
                self._buffer.remove(0, eol_end)
            else:
                self._buffer.clear()
            logger.debug(f'emitting {data}')
            self.dataReady.emit(data.decode('utf-8', 'backslashreplace'))
        else:
            logger.debug(f'buffered {bytes(self._buffer)}')
