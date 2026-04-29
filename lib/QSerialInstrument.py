import logging

from qtpy.QtSerialPort import QSerialPortInfo
from QInstrument.lib.QAbstractInstrument import QAbstractInstrument
from QInstrument.lib.QSerialInterface import QSerialInterface


logger = logging.getLogger(__name__)


class QSerialInstrument(QAbstractInstrument):
    '''Base class for instruments connected via serial ports.

    Extends :class:`QAbstractInstrument` with a serial transport layer
    and command-response communication helpers.  Holds a
    :class:`QSerialInterface` by composition and delegates raw I/O
    through it.  Concrete instrument classes inherit from this, declare
    a :attr:`comm` class attribute with serial parameters, and override
    :meth:`identify` to verify the connected device.

    The full communication API available to concrete instruments is:

    - :meth:`transmit` — send a command with no response expected
    - :meth:`handshake` — send a command and return the raw response
    - :meth:`expect` — send a command and test the response string
    - :meth:`getValue` — send a command and return a typed value

    All four methods are defined here.  A future transport subclass
    (e.g. ``QGPIBInstrument``) would provide the same API over a
    different physical layer.

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

    # Re-export serial enum types for convenient access in subclasses
    BaudRate = QSerialInterface.BaudRate
    DataBits = QSerialInterface.DataBits
    StopBits = QSerialInterface.StopBits
    Parity = QSerialInterface.Parity
    FlowControl = QSerialInterface.FlowControl

    comm: dict = {}

    def __init__(self, portName: str | None = None, **kwargs) -> None:
        super().__init__()
        args = self.comm | kwargs
        self._interface = QSerialInterface(parent=self, **args)
        if portName:
            self.open(portName)

    def __repr__(self) -> str:
        name = self.__class__.__name__
        if self.isOpen():
            port = self._interface.portName()
        else:
            port = 'not connected'
        return f'{name}({port})'

    def identify(self) -> bool:
        '''Return True if the connected device is the expected instrument.

        The base implementation always returns ``True``.  Subclasses
        should override this to query the device and verify its identity.

        Returns
        -------
        bool
            ``True`` if the device is recognized, ``False`` otherwise.
        '''
        return True

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
            logger.debug(f'Device on {portName} is not '
                         f'{self.__class__.__name__}')
            self._interface.close()
        return self._interface.isOpen()

    def isOpen(self) -> bool:
        '''Return True if the serial interface is currently open.'''
        return self._interface.isOpen()

    def close(self) -> None:
        '''Close the serial interface.'''
        self._interface.close()

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

    def handshake(self, data: str, **kwargs) -> str:
        '''Transmit a command and return the instrument's response.

        Parameters
        ----------
        data : str
            Command string to send to the instrument.
        **kwargs :
            Passed through to :meth:`receive`.

        Returns
        -------
        str
            Stripped response string from the instrument.
        '''
        self.transmit(data)
        return self.receive(**kwargs).strip()

    def expect(self, query: str, response: str, **kwargs) -> bool:
        '''Return True if the instrument's response contains *response*.

        Parameters
        ----------
        query : str
            Command string to send to the instrument.
        response : str
            Substring expected in the instrument's reply.
        **kwargs :
            Passed through to :meth:`receive`.

        Returns
        -------
        bool
            ``True`` if *response* appears in the instrument's reply.
        '''
        return response in self.handshake(query, **kwargs)

    def getValue(self, query: str,
                 dtype: type = float
                 ) -> QAbstractInstrument.PropertyValue | None:
        '''Query the instrument and return a typed value.

        Parameters
        ----------
        query : str
            Command string that elicits a single-value response.
        dtype : type, optional
            Converts the response string to the desired type.
            Default: ``float``.

        Returns
        -------
        PropertyValue or None
            Value converted by *dtype*, or ``None`` if conversion fails.
        '''
        response = self.handshake(query)
        try:
            value = dtype(response)
        except (ValueError, TypeError):
            value = None
        return value

    @classmethod
    def example(cls, portname: str | None = None) -> None:
        '''Connect to an instrument and print its current settings.

        Creates a ``QCoreApplication``, opens the instrument on *portname*
        (or auto-detects it with :meth:`find` when *portname* is ``None``),
        then prints the instrument repr.

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
        QCoreApplication.instance() or QCoreApplication([])
        instrument = cls().find() if portname is None else cls(portname)
        if not instrument.isOpen():
            print(f'{cls.__name__}: instrument not found.')
            return
        print(instrument)


__all__ = ['QSerialInstrument']
