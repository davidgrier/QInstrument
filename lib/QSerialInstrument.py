from QInstrument.lib.QAbstractInstrument import QAbstractInstrument
from QInstrument.lib.QSerialInterface import QSerialInterface


class QSerialInstrument(QAbstractInstrument, QSerialInterface):
    '''Base class for instruments connected to serial ports.

    Combines :class:`QAbstractInstrument` (property registration, thread-safe
    access) with :class:`QSerialInterface` (serial I/O, port auto-detection).
    Concrete instrument classes inherit from this and call
    ``registerProperty()`` in ``__init__`` for each controllable parameter.

    See Also
    --------
    QAbstractInstrument, QSerialInterface
    '''

    def __init__(self, portName: str | None = None, **kwargs) -> None:
        super().__init__(portName=portName or '', **kwargs)

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
        if portname is None:
            instrument = cls().find()
        else:
            instrument = cls(portname)
        print(instrument)


if __name__ == '__main__':
    QSerialInstrument.example()
