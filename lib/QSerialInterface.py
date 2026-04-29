from __future__ import annotations

import logging

from qtpy import QtCore
from qtpy.QtSerialPort import QSerialPort


logger = logging.getLogger(__name__)


class QSerialInterface(QSerialPort):
    '''Serial port wrapper providing framed I/O for instrument communication.

    Wraps ``QSerialPort`` to provide raw serial I/O with custom
    end-of-line handling for :meth:`transmit` and :meth:`receive`.
    Intended to run in a dedicated worker thread owned by
    :class:`QSerialInstrument`; port discovery and device identification
    are handled by the instrument layer, not here.

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

    Examples
    --------
    >>> iface = QSerialInterface(eol='\\n')
    >>> iface.open('ttyUSB0')
    '''

    BaudRate = QSerialPort.BaudRate
    DataBits = QSerialPort.DataBits
    StopBits = QSerialPort.StopBits
    Parity = QSerialPort.Parity
    FlowControl = QSerialPort.FlowControl

    def __init__(self,
                 portName: str = '',
                 eol: bytes | str = '',
                 timeout: int | None = None,
                 baudRate: QSerialPort.BaudRate | None = None,
                 dataBits: QSerialPort.DataBits | None = None,
                 stopBits: QSerialPort.StopBits | None = None,
                 parity: QSerialPort.Parity | None = None,
                 flowControl: QSerialPort.FlowControl | None = None,
                 **kwargs) -> None:
        super().__init__(**kwargs)
        if baudRate is not None:
            # PyQt6 enums expose .value; PyQt5 enums need int()
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

        Intended to run in a dedicated worker thread (see
        :class:`QInstrumentWidget`), where blocking the thread with
        :meth:`waitForReadyRead` is correct and prevents reentrancy.

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
            if not self.bytesAvailable():
                if not self.waitForReadyRead(self.timeout):
                    logger.debug('Timeout waiting for response')
                    break
            buffer += bytes(self.readAll())
            if eol and eol in buffer:
                buffer = buffer[:buffer.index(eol)]
                break
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
        buffer = b''
        while len(buffer) < n:
            if not self.bytesAvailable():
                if not self.waitForReadyRead(self.timeout):
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


__all__ = ['QSerialInterface']
