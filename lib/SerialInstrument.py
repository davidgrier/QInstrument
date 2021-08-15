from PyQt5.QtCore import (pyqtSlot, pyqtSignal)
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
    eol: str
        End-of-line string (character) used to terminate
        strings that are transmitted to the instrument.
        Default: ''
    timeout0: float
        Time to wait for initial characters from device [ms]
        Default: 1000.
    timeout1: float
        Time to wait for subsequent characters [ms]
        Default: 100.

    Example
    -------
    >>> instrument = SerialInstrument().find()

    '''
    
    def __init__(self,
                 portName=None,
                 eol='',
                 timeout0=None,
                 timeout1=None,
                 **kwargs):
        super().__init__(**kwargs)
        self.eol = eol
        self.timeout0 = timeout0 or 1000.
        self.timeout1 = timeout1 or 100. 
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
            return
        self.setPortName(portName)
        if super().open(QSerialPort.ReadWrite):
            self.clear()
            if not self.identify():
                msg = 'Device on {} does not identify as {}'
                logger.warning(msg.format(portName, self.__class__.__name__))
                self.close()
        else:
            logger.warning(f'Could not open {portName}')

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
        ports = QSerialPortInfo.availablePorts()
        names = [port.portName() for port in ports]
        for name in names:
            self.open(name)
            if self.isOpen():
                return self
        logger.error('Could not find {}'.format(self.__class__.__name__))
        return None
    
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
            cmd = data + self.eol
            self.write(bytes(cmd, 'utf-8'))
        else:
            self.write(data)
        self.flush()
        logger.debug(f' sent: {data}')

    def receive(self, raw=False, breakoneol=False):
        '''Receive data from the instrument

        Keywords
        --------
        raw: bool
            True: Return raw data as bytes
            False: Decode data into str [Default]
        breakoneol: bool
            True: Return as soon as eolcharacter appears
            False: Wait for timeout.

        Returns
        -------
        response: str | bytes
            Data received from the instrument.
        '''
        if not self.waitForReadyRead(self.timeout0):
            return ''
        response = self.readAll()
        while (self.waitForReadyRead(self.timeout1)):
            response.append(self.readAll())
            if breakoneol and (self.eol in response):
                break
        logger.debug(f' received: {response}')
        if raw:
            return response.data()
        else:
            return response.data().decode('utf-8')

    def handshake(self, cmd, raw=False, breakoneol=False):
        '''Send command to the instrument and receive its response

        Arguments
        ---------
        command: str
            String to be communicated to the instrument that
            will elicit a response.

        Keywords
        --------
        raw: bool
            True: Return raw data as bytes
            False: Decode data into str [Default]
        breakoneol: bool
            True: Return as soon as eolcharacter appears
            False: Wait for timeout.

        Returns
        -------
        response: str | bytes
            Response from instrument
        '''
        self.send(cmd)
        return self.receive(raw=raw, breakoneol=breakoneol)

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
        return dtype(self.handshake(query).strip())

    @pyqtSlot(object)
    def set_value(self, value):
        name = str(self.sender().objectName())
        if hasattr(self, name):
            setattr(self, name, value)
        else:
            msg = f'Failed to set {name} ({value}): Not a valid property'
            logger.warning(msg)
