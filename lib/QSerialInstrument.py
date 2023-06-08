from QInstrument.lib.QInstrumentMixin import QInstrumentMixin
from QInstrument.lib.QSerialInterface import QSerialInterface


class QSerialInstrument(QInstrumentMixin, QSerialInterface):
    '''Base class for instruments connected to serial ports

    ........

    Inherits
    --------
    QInstrument.lib.QInstrumentMixin
    QInstrument.lib.QSerialInterface

    Properties
    ----------
    eol: str
        End-of-line string (character) used to terminate
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
    pass


def example(portname='/dev/ttyUSB0'):
    from PyQt5.QtCore import QCoreApplication

    app = QCoreApplication([])

    comm = dict(baudRate=QSerialInstrument.Baud9600,
                dataBits=QSerialInstrument.Data8,
                stopBits=QSerialInstrument.OneStop,
                parity=QSerialInstrument.NoParity,
                flowControl=QSerialInstrument.NoFlowControl,
                eol=b'\r')

    a = QSerialInstrument(portname, **comm)
    print(a.handshake('*IDN?'))


if __name__ == '__main__':
    example()
