from qtpy import QtCore

from QInstrument.lib.QInstrumentWorker import QInstrumentWorker


class QSR830Worker(QInstrumentWorker):
    '''Polls an SR830 lock-in amplifier at maximum rate in a worker thread.

    Emits :attr:`measurement` on every poll tick with the simultaneous
    snapshot from ``SNAP?9,3,4``.

    Signals
    -------
    measurement : list[float]
        ``[frequency [Hz], R [V], theta [degrees]]`` captured atomically
        via the SR830 SNAP command.

    Example
    -------
    .. code-block:: python

        worker = QSR830Worker(device)
        worker.measurement.connect(self._onMeasurement)
        start_button.clicked.connect(worker.startPolling)
        stop_button.clicked.connect(worker.stopPolling)
    '''

    measurement = QtCore.Signal(list)

    def poll(self) -> None:
        '''Capture one snapshot and emit :attr:`measurement`.'''
        self.measurement.emit(self.instrument.report())


if __name__ == '__main__':
    QSR830Worker.example()

__all__ = ['QSR830Worker']
