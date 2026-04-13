from qtpy import QtCore

from QInstrument.lib.QInstrumentWorker import QInstrumentWorker


class QSR844Worker(QInstrumentWorker):
    '''Polls an SR844 RF lock-in amplifier at maximum rate in a worker thread.

    Emits :attr:`measurement` on every poll tick with the simultaneous
    snapshot from ``SNAP?9,3,4``.

    Signals
    -------
    measurement : list[float]
        ``[frequency [Hz], R [V], theta [degrees]]`` captured atomically
        via the SR844 SNAP command.

    Example
    -------
    .. code-block:: python

        worker = QSR844Worker(device)
        worker.measurement.connect(self._onMeasurement)
        start_button.clicked.connect(worker.startPolling)
        stop_button.clicked.connect(worker.stopPolling)
    '''

    measurement = QtCore.Signal(list)

    def poll(self) -> None:
        '''Capture one snapshot and emit :attr:`measurement`.'''
        self.measurement.emit(self.instrument.report())


if __name__ == '__main__':
    QSR844Worker.example()

__all__ = ['QSR844Worker']
