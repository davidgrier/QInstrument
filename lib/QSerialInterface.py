from __future__ import annotations

import logging

from qtpy import QtCore
from qtpy.QtSerialPort import QSerialPort


logger = logging.getLogger(__name__)


class QSerialInterface(QSerialPort):
    '''Base class for instruments connected to serial ports.

    Wraps ``QSerialPort`` to provide raw serial I/O with custom
    end-of-line handling for :meth:`transmit` and :meth:`receive`,
    and optional non-blocking (signal-driven) I/O.

    Port discovery and device identification are handled by the
    instrument layer (:class:`QSerialInstrument`), not here.

    Parameters
    ----------
    portName : str
        Name of the serial port to open on construction, without the
        system-dependent path prefix (e.g. ``'ttyUSB0'``, ``'COM1'``).
        Pass an empty string (default) to skip opening on construction.
    eol : bytes | str
        End-of-line sequence appended to outgoing strings by
        :meth:`transmit` and used as the read terminator by
        :meth:`receive`. Default: ``''`` (no terminator).
    timeout : int | None
        Milliseconds to wait for incoming data before giving up.
        Default: ``None``, which is treated as ``100`` ms.
    blocking : bool
        If ``True`` (default), I/O is synchronous (polling).
        If ``False``, incoming data is handled by the
        :attr:`dataReady` signal.
    baudRate : QSerialPort.BaudRate | None
        Port baud rate. Uses the ``QSerialPort`` default if ``None``.
    dataBits : QSerialPort.DataBits | None
        Number of data bits. Uses the ``QSerialPort`` default if ``None``.
    stopBits : QSerialPort.StopBits | None
        Number of stop bits. Uses the ``QSerialPort`` default if ``None``.
    parity : QSerialPort.Parity | None
        Parity mode. Uses the ``QSerialPort`` default if ``None``.
    flowControl : QSerialPort.FlowControl | None
        Flow control mode. Uses the ``QSerialPort`` default if ``None``.

    Attributes
    ----------
    eol : bytes
        End-of-line sequence used for read/write termination.
    timeout : int
        Read timeout in milliseconds.
    blocking : bool
        Toggles between synchronous polling and signal-driven I/O.
    BaudRate : type
        Alias for ``QSerialPort.BaudRate``. Use as
        ``QSerialInstrument.BaudRate.Baud9600`` in ``comm`` dicts.
    DataBits : type
        Alias for ``QSerialPort.DataBits``.
    StopBits : type
        Alias for ``QSerialPort.StopBits``.
    Parity : type
        Alias for ``QSerialPort.Parity``.
    FlowControl : type
        Alias for ``QSerialPort.FlowControl``.

    Signals
    -------
    dataReady(str)
        Emitted in non-blocking mode when a complete line (terminated
        by :attr:`eol`) has been received.

    Examples
    --------
    Synchronous use:

    >>> iface = QSerialInterface(eol='\\n')
    >>> iface.open('ttyUSB0')

    Non-blocking use with a signal handler:

    >>> iface = QSerialInterface(eol='\\n', blocking=False)
    >>> iface.dataReady.connect(handle_response)
    >>> iface.open('ttyUSB0')
    '''

    dataReady = QtCore.Signal(str)

    BaudRate = QSerialPort.BaudRate
    DataBits = QSerialPort.DataBits
    StopBits = QSerialPort.StopBits
    Parity = QSerialPort.Parity
    FlowControl = QSerialPort.FlowControl

    def __init__(self,
                 portName: str = '',
                 eol: bytes | str = '',
                 timeout: int | None = None,
                 blocking: bool = True,
                 baudRate: QSerialPort.BaudRate | None = None,
                 dataBits: QSerialPort.DataBits | None = None,
                 stopBits: QSerialPort.StopBits | None = None,
                 parity: QSerialPort.Parity | None = None,
                 flowControl: QSerialPort.FlowControl | None = None,
                 **kwargs) -> None:
        super().__init__(**kwargs)
        if baudRate is not None:
            self.setBaudRate(baudRate.value if hasattr(baudRate, 'value') else int(baudRate))
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

    def open(self, portName: str) -> bool:
        '''Open the serial port for read/write access.

        Parameters
        ----------
        portName : str
            Name of the serial port device file, without the
            system-dependent path prefix.
            Examples: ``'ttyUSB0'``, ``'COM1'``.

        Returns
        -------
        bool
            ``True`` if the port was opened successfully.
        '''
        if not portName:
            return False
        self.setPortName(portName)
        if not super().open(QSerialPort.OpenModeFlag.ReadWrite):
            logger.debug(f'Could not open {portName}')
            return False
        self.clear()
        return True

    @property
    def blocking(self) -> bool:
        '''bool: ``True`` for synchronous polling I/O; ``False`` for
        signal-driven I/O via :attr:`dataReady`.
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
        the read times out.  The EOL bytes are stripped from the returned
        value.

        Waiting is performed via a local ``QEventLoop`` driven by
        ``readyRead`` and a ``QTimer``, so the main event loop remains
        alive during the wait and the GUI stays responsive.

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
        loop = QtCore.QEventLoop()
        timer = QtCore.QTimer()
        timer.setSingleShot(True)
        timer.timeout.connect(loop.quit)
        self.readyRead.connect(loop.quit)
        buffer = b''
        while True:
            if not self.bytesAvailable():
                timer.start(self.timeout)
                loop.exec()
                timer.stop()
                if not self.bytesAvailable():
                    logger.debug('Timeout waiting for response')
                    break
            buffer += bytes(self.readAll())
            if eol and eol in buffer:
                buffer = buffer[:buffer.index(eol)]
                break
        self.readyRead.disconnect(loop.quit)
        return buffer if raw else buffer.decode('utf-8', errors='replace')

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
        loop = QtCore.QEventLoop()
        timer = QtCore.QTimer()
        timer.setSingleShot(True)
        timer.timeout.connect(loop.quit)
        self.readyRead.connect(loop.quit)
        buffer = b''
        while len(buffer) < n:
            if not self.bytesAvailable():
                timer.start(self.timeout)
                loop.exec()
                timer.stop()
                if not self.bytesAvailable():
                    logger.warning('Timeout waiting for response')
                    break
            buffer += bytes(self.readAll())
        self.readyRead.disconnect(loop.quit)
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


__all__ = ['QSerialInterface']
