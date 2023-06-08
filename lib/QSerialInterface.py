from PyQt5.QtCore import (pyqtProperty, pyqtSlot, pyqtSignal, QByteArray)
from PyQt5.QtSerialPort import (QSerialPort, QSerialPortInfo)
import logging


logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)


class QSerialInterface(QSerialPort):
    '''Base class for instruments connected to serial ports

    ........

    Inherits
    --------
    PyQt5.QtSerialPort.QSerialPort

    Properties
    ----------
    eol: bytes
        End-of-line character used to terminate
        strings that are transmitted to the instrument.
        Default: ''
    timeout: float
        Time to wait for characters from device [ms]
        Default: 100.

    Methods
    -------
    find(): QSerialInstrument
        Poll serial ports to find the device.

    Signals
    -------
    dataReady(str):
        Emitted when asynchronous reading encounters
        the eol character and transmits the received data
        up to and including the eol character.

    Slots
    -----
    set_value(value):
        Intended as a slot for instrument widgets that
        subclass QSerialInstrument.

    Example
    -------
    >>> instrument = QSerialInstrument().find()

    '''

    dataReady = pyqtSignal(str)

    def __init__(self,
                 portName=None,
                 eol='',
                 timeout=None,
                 blocking=True,
                 **kwargs):
        super().__init__(**kwargs)
        self.eol = eol if isinstance(eol, bytes) else eol.encode()
        self.timeout = timeout or 100
        self.blocking = blocking
        self._buffer = QByteArray()
        self.open(portName)

    def identify(self, **kwargs):
        '''Returns true if communication with instrument succeeds

        This method should be overridden by subclasses.
        '''
        return True

    def open(self, portName, **kwargs):
        '''Open serial communications with instrument.

        open() succeeds if the specified port can be opened
        in read/write mode, and if identify() returns True.
        Subclasses of SerialInstrument are responsible for
        overriding identify() to poll the instrument and
        to ascertain that it is the correct device.

        Arguments
        ---------
        portName: str
            Name of the serial port device file, without
            system-dependent path.
            Examples: 'ttyUSB0', 'COM1'

        kwargs: optional
            Open accepts keyword arguments for identify(),
            which must be defined by a subclassed instrument implementation.
        '''
        if portName is None:
            return False
        self.setPortName(portName)
        if super().open(QSerialPort.ReadWrite):
            self.clear()
            if not self.identify(**kwargs):
                className = self.__class__.__name__
                msg = f'Device on {portName} is not {className}'
                logger.warning(msg)
                self.close()
        else:
            logger.warning(f'Could not open {portName}')
        return self.isOpen()

    def find(self, **kwargs):
        '''Poll all serial ports to identify suitable instrument

        find() calls open() on each serial port on the system
        until it either succeeds or exhausts all possibilities.

        Arguments
        ---------
        kwargs: optional
            find() accepts keyword arguments for identify(),
            which must be defined by a subclassed instrument implementation.

        Returns
        -------
        instrument: SerialInstrument
            Reference to the instrument object
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

    @pyqtProperty(bool)
    def blocking(self):
        return self._blocking

    @blocking.setter
    def blocking(self, blocking):
        if blocking:
            try:
                self.readyRead.disconnect(self._handleReadyRead)
            except TypeError:
                pass
        else:
            self.readyRead.connect(self._handleReadyRead)
        self._blocking = blocking

    def transmit(self, data):
        '''Transmit data to the instrument

        Arguments
        ---------
        data: str | bytes
            Data to be transmitted. Most data takes
            the form of strings that represent commands
            or queries to the instrument. A data string
            will be terminated with eol.

            Data provided as bytes are transmitted
            without eol termination.
        '''
        if not self.isOpen():
            logger.warn('Cannot send data: Device is not open.')
            return
        if isinstance(data, str):
            data = data.encode() + self.eol
        self.write(data)
        self.flush()
        logger.debug(f' sent: {data}')

    def receive(self, eol=None, raw=False):
        '''Read from serial interface until end of line

        Keywords
        --------
        eol: bytes
           end-of-line character
        raw: bool
           True: return line as bytes
           False: decode response from instrument
           Default: False

        Returns
        -------
        line: str | bytes
           characters received from serial interface
        '''
        eol = eol or self.eol
        buffer = b''
        while self.bytesAvailable() or self.waitForReadyRead(self.timeout):
            char = bytes(self.read(1))
            if char == eol:
                break
            buffer += char
        return buffer if raw else buffer.decode()

    def readn(self, n=1):
        '''Receive n bytes of data from the instrument

        Keywords
        --------
        n: int
            Number of bytes to receive

        Returns
        -------
        response: bytes
            Data received from the instrument
        '''
        if not self.isOpen():
            logger.warn('Cannot read data: Device is not open.')
            return b''
        buffer = b''
        while self.bytesAvailable() or self.waitForReadyRead(self.timeout):
            char = bytes(self.read(1))
            buffer += char
            if len(buffer) >= n:
                break
        return buffer

    @pyqtSlot()
    def _handleReadyRead(self):
        '''Slot for nonblocking data communication'''
        self._buffer.append(self.readAll())
        if self._buffer.contains(self.eol):
            pos = self._buffer.indexOf(self.eol) + 1
            if pos < self._buffer.size():
                data = bytes(self._buffer.left(pos))
                self._buffer.remove(0, pos)
            else:
                data = bytes(self._buffer)
                self._buffer.clear()
            logger.debug('emitting {}'.format(data.decode('utf-8')))
            self.dataReady.emit(data.decode('utf-8', 'backslashreplace'))
        else:
            logger.debug(f'buffered {self.buffer}')
