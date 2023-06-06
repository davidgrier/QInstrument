from QInstrument.lib.QInstrument import QInstrument
from QInstrument.lib.QSerialInterface import QSerialInterface
import logging


logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)


class QSerialInstrument(QInstrument):
    '''Base class for instruments connected to serial ports

    ........

    Inherits
    --------
    QInstrument.lib.QInstrument

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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.interface = QSerialInterface(**kwargs)
