from PyQt5.QtCore import (pyqtSlot, pyqtSignal, QByteArray)
from PyQt5.QtSerialPort import (QSerialPort, QSerialPortInfo)
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)


class SerialInstrument(QSerialPort):
    '''Base class for instruments connected to serial ports

    ........

    Inherits
    --------
    PyQt5.QtSerialPort.QSerialPort

    Properties
    ----------
    eol: bytes
        End-of-line string (character) used to terminate
        strings that are transmitted to the instrument.
        Default: b''
    timeout: float
        Time to wait for characters from device [ms]
        Default: 100.

    Example
    -------
    >>> instrument = SerialInstrument().find()

    '''

    dataReady = pyqtSignal(str)

    def __init__(self,
                 portName=None,
                 eol=b'',
                 timeout=None,
                 **kwargs):
        super().__init__(**kwargs)
        self.eol = eol.encode()
        self.timeout = timeout or 100.
        self.buffer = QByteArray()
        self.open(portName)

    def open(self, portName):
        '''Open serial communications with instrument.

        open() succeeds if the specified port can be opened
        in read/write mode, and if identify() returns True.
        Subclasses of SerialInstrument are responsible for
        overriding identify() to poll the instrument and
        to ascertain that it is the correct device.

        Arguments
        ---------
        portName: str, optional
            Name of the serial port device file, without
            system-dependent path.
            Examples: 'ttyUSB0', 'COM1'
        '''
        if portName is None:
            return False
        self.setPortName(portName)
        if super().open(QSerialPort.ReadWrite):
            self.clear()
            if not self.identify():
                className = self.__class__.__name__
                msg = f'Device on {portName} is not {className}'
                logger.warning(msg)
                self.close()
        else:
            logger.warning(f'Could not open {portName}')
        return self.isOpen()

    def find(self):
        '''Poll all serial ports to identify suitable instrument

        find() calls open() on each serial port on the system
        until it either succeeds or exhausts all possibilities.

        Returns
        -------
        instrument: SerialInstrument | None
            Reference to the instrument object, if found,
            else None if no instruments are identified
        '''
        for port in QSerialPortInfo.availablePorts():
            logger.debug('Trying to open {}'.format(port.portName()))
            if self.open(port.portName()):
                break
        else:
            logger.error('Could not find {}'.format(self.__class__.__name__))
        return self

    def send(self, data):
        '''Send data to the instrument

        Arguments
        ---------
        data: str | bytes
            Data to be communicated. Most data takes
            the form of strings that represent commands
            or queries to the instrument. A data string
            will be terminated with the eol string.

            Data provided as bytes are transmitted
            without eol termination.
        '''
        if type(data) == str:
            data = data.encode() + self.eol
        self.write(data)
        self.flush()
        logger.debug(f' sent: {data}')

    def read_until(self, eol=None, raw=False):
        '''Receive data from the instrument

        Keywords
        --------
        eol: bytes [optional]
            End-of-line character
            Default: self.eol
        raw: bool [optional]
            True: Return raw data as bytes
            False: Decode data into str [Default]

        Returns
        -------
        response: str | bytes
            Data received from the instrument.
        '''
        eol = eol or self.eol
        buffer = b''
        while self.bytesAvailable() or self.waitForReadyRead(self.timeout):
            char = bytes(self.read(1))
            buffer += char
            if char == eol:
                break
        logger.debug(f' received: {buffer}')
        if raw:
            return buffer
        return buffer.decode('utf-8').strip()

    def handshake(self, query, raw=False):
        '''Send command to the instrument and receive its response

        Arguments
        ---------
        query: str
            String to be communicated to the instrument that
            will elicit a response.

        Keywords
        --------
        raw: bool
            True: Return raw data as bytes
            False: Decode data into str [Default]

        Returns
        -------
        response: str | bytes
            Response from instrument
        '''
        self.blockSignals(True)
        self.send(query)
        response = self.read_until(raw=raw)
        self.blockSignals(False)
        return response

    def expect(self, query, response):
        '''Send query and check for anticipated response

        Arguments
        ---------
        query: str
            Command to instrument that will elicit response.
        response: str
            Anticipated response

        Returns
        -------
        expect: bool
            True: expected response was received
            False: expected response was not received
        '''
        return response in self.handshake(query)

    def get_value(self, query, dtype=float):
        '''Send query and return response in specified data type

        Arguments
        ---------
        query: str
            Command to instrument that will elicit response.
        dtype: type [optional]
            Anticipated type of returned data.
            Default: float

        Returns
        -------
        value: dtype
            Value elicited from instrument by query
        '''
        response = self.handshake(query)
        try:
            value = dtype(response)
        except ValueError:
            value = None
            logger.error(f'Could not parse {response}')
        return value

    @pyqtSlot()
    def receive(self):
        self.buffer.append(self.readAll())
        if self.buffer.contains(self.eol):
            len = self.buffer.indexOf(self.eol) + 1
            if len < buffer.size():
                data = bytes(self.buffer.left(len)).decode('utf-8')
                self.buffer.remove(0, len)
            else:
                data = bytes(self.buffer).decode('utf-8')
                self.buffer.clear()
            self.dataReady.emit(data)

    @pyqtSlot(object)
    def set_value(self, value):
        name = str(self.sender().objectName())
        if hasattr(self, name):
            setattr(self, name, value)
        else:
            msg = f'Failed to set {name} ({value}): Not a valid property'
            logger.warning(msg)

    def identify(self):
        '''Identify intended instrument

        Subclasses are responsible for overriding identify().

        Returns
        -------
        identify: bool
            True: specified instrument is connected to the serial port
            False: instrument on the port failed to identify correctly
        '''
        return True
