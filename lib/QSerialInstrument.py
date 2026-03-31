from QInstrument.lib.QAbstractInstrument import QAbstractInstrument
from QInstrument.lib.QSerialInterface import QSerialInterface


class QSerialInstrument(QAbstractInstrument, QSerialInterface):
    '''Base class for instruments connected to serial ports

    ........


    Properties
    ----------
    eol: bytes
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

    @classmethod
    def example(cls, portname: str = '/dev/ttyUSB0') -> None:
        from qtpy import QtCore

        for k in cls.__dict__.keys():
            if 'Baud' in k:
                print(dir(k))
        '''
        app = QtCore.QCoreApplication([])

        comm = dict(baudRate=cls.BaudRate.Baud9600,
                    dataBits=cls.DataBits.Data8,
                    stopBits=cls.StopBits.OneStop,
                    parity=cls.Parity.NoParity,
                    flowControl=cls.FlowControl.NoFlowControl,
                    eol=b'\r')

        a = cls(portname, **comm)
        print(a._handshake('*IDN?'))
        '''


if __name__ == '__main__':
    QSerialInstrument.example()
