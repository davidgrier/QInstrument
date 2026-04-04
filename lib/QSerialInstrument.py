import logging

from qtpy.QtSerialPort import QSerialPortInfo
from QInstrument.lib.QAbstractInstrument import QAbstractInstrument
from QInstrument.lib.QSerialInterface import QSerialInterface


logger = logging.getLogger(__name__)


class QSerialInstrument(QAbstractInstrument):
    '''Base class for instruments connected via serial ports.

    Holds a :class:`QSerialInterface` by composition and delegates all
    I/O through it.  Concrete instrument classes inherit from this,
    declare a :attr:`comm` class attribute with serial parameters, and
    override :meth:`identify` to verify the connected device.

    Because the interface is a separate object, the same instrument class
    can be instantiated with different transports (e.g. RS-232 today,
    GPIB tomorrow) simply by swapping out the interface.

    Attributes
    ----------
    comm : dict
        Serial parameters passed to :class:`QSerialInterface` on
        construction.  Subclasses define this as a class attribute using
        the enum aliases re-exported here (e.g.
        ``baudRate=QSerialInstrument.BaudRate.Baud9600``).
    BaudRate : type
        Alias for ``QSerialPort.BaudRate``.
    DataBits : type
        Alias for ``QSerialPort.DataBits``.
    StopBits : type
        Alias for ``QSerialPort.StopBits``.
    Parity : type
        Alias for ``QSerialPort.Parity``.
    FlowControl : type
        Alias for ``QSerialPort.FlowControl``.
    '''

    # Re-export serial enum types so subclass comm dicts need no extra imports.
    BaudRate    = QSerialInterface.BaudRate
    DataBits    = QSerialInterface.DataBits
    StopBits    = QSerialInterface.StopBits
    Parity      = QSerialInterface.Parity
    FlowControl = QSerialInterface.FlowControl

    comm: dict = {}

    def __init__(self, portName: str | None = None, **kwargs) -> None:
        super().__init__()
        self._interface = QSerialInterface(**(self.comm | kwargs))
        if portName:
            self.open(portName)

    def identify(self) -> bool:
        '''Return True if the connected device is the expected instrument.

        The base implementation always returns ``True``.  Subclasses
        should override this to query the device and verify its identity
        (e.g. via ``*IDN?``).

        Returns
        -------
        bool
            ``True`` if the device is recognized, ``False`` otherwise.
        '''
        return True

    def transmit(self, data: str | bytes) -> None:
        '''Transmit data to the instrument via the serial interface.

        Parameters
        ----------
        data : str | bytes
            Data to send.  See :meth:`QSerialInterface.transmit`.
        '''
        self._interface.transmit(data)

    def receive(self, **kwargs) -> str | bytes:
        '''Read a response from the instrument via the serial interface.

        Parameters
        ----------
        **kwargs
            Passed through to :meth:`QSerialInterface.receive`.

        Returns
        -------
        str | bytes
            Response from the instrument.
        '''
        return self._interface.receive(**kwargs)

    def open(self, portName: str) -> bool:
        '''Open a specific serial port and verify the connected device.

        Opens *portName* via the interface, then calls :meth:`identify`.
        Closes the port and returns ``False`` if identification fails.

        Parameters
        ----------
        portName : str
            Serial port name without the system path prefix
            (e.g. ``'ttyUSB0'``, ``'COM1'``).

        Returns
        -------
        bool
            ``True`` if the port is open and the device identified.
        '''
        if not self._interface.open(portName):
            return False
        if not self.identify():
            logger.warning(f'Device on {portName} is not '
                           f'{self.__class__.__name__}')
            self._interface.close()
        return self._interface.isOpen()

    def find(self) -> 'QSerialInstrument':
        '''Scan all available serial ports to locate the instrument.

        Calls :meth:`open` on each port returned by
        ``QSerialPortInfo.availablePorts()`` until one succeeds.

        Returns
        -------
        QSerialInstrument
            The instance itself, whether or not a device was found.
            Call :meth:`isOpen` to check the result.
        '''
        for port in QSerialPortInfo.availablePorts():
            portName = port.portName()
            logger.debug(f'Trying {portName}')
            if self.open(portName):
                break
        else:
            logger.error(f'Could not find {self.__class__.__name__}')
        return self

    def isOpen(self) -> bool:
        '''Return True if the serial interface is currently open.'''
        return self._interface.isOpen()

    def close(self) -> None:
        '''Close the serial interface.'''
        self._interface.close()

    @classmethod
    def example(cls, portname: str | None = None) -> None:
        '''Connect to an instrument and print its current settings.

        Creates a ``QCoreApplication``, opens the instrument on *portname*
        (or auto-detects it with :meth:`find` when *portname* is ``None``),
        then prints the instrument repr showing all registered property values.

        Intended to be run from ``__main__`` in each instrument module:

        .. code-block:: python

            if __name__ == '__main__':
                QMyInstrument.example()

        Parameters
        ----------
        portname : str | None, optional
            Serial port to open (e.g. ``'/dev/ttyUSB0'``).
            If ``None``, all available ports are scanned via :meth:`find`.
        '''
        from qtpy.QtCore import QCoreApplication
        app = QCoreApplication.instance() or QCoreApplication([])
        instrument = cls().find() if portname is None else cls(portname)
        if not instrument.isOpen():
            print(f'{cls.__name__}: instrument not found or not connected.')
            return
        print(instrument)


if __name__ == '__main__':
    QSerialInstrument.example()
