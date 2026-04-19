from __future__ import annotations

import logging
import warnings
from qtpy import QtCore

logger = logging.getLogger(__name__)


class QInstrumentWorker(QtCore.QObject):
    '''Runs a QAbstractInstrument in a dedicated QThread with a poll loop.

    The instrument is moved into the worker thread on construction.
    All serial I/O therefore occurs off the GUI thread, preventing
    ``waitForReadyRead()`` from blocking the event loop.

    Subclass and override :meth:`poll` to define continuous measurement
    behaviour.  Connect :meth:`startPolling` and :meth:`stopPolling` via
    signals from the widget — Qt uses a queued connection automatically
    once the worker has been moved to its thread, serialising all access
    to the instrument.

    Parameters
    ----------
    instrument : QAbstractInstrument
        Instrument to run in the worker thread.  After construction the
        instrument must not be accessed directly from any other thread;
        use signal/slot connections instead.

    Example
    -------
    .. code-block:: python

        class SR830Worker(QInstrumentWorker):
            measurement = Signal(list)   # [frequency, R, theta]

            def poll(self) -> None:
                self.measurement.emit(self.instrument.report())

        worker = SR830Worker(device)
        worker.measurement.connect(self._onMeasurement)
        start_button.clicked.connect(worker.startPolling)
        stop_button.clicked.connect(worker.stopPolling)
    '''

    def __init__(self, instrument, parent=None) -> None:
        warnings.warn(
            'QInstrumentWorker is deprecated and will be removed in a future '
            'release. QSerialInterface.receive() no longer blocks the event '
            'loop, so instrument polling does not require a worker thread.',
            DeprecationWarning,
            stacklevel=2
        )
        super().__init__(parent)
        self._instrument = instrument
        self._thread = QtCore.QThread()
        self._thread.setObjectName(f'{type(instrument).__name__}Thread')
        instrument.moveToThread(self._thread)
        self.moveToThread(self._thread)
        self._thread.started.connect(self._setup)
        self._thread.start()

    @property
    def instrument(self):
        '''The instrument running in the worker thread.'''
        return self._instrument

    @QtCore.Slot()
    def _setup(self) -> None:
        '''Create the poll timer inside the worker thread.

        Called once via the ``thread.started`` queued connection, before
        any other queued calls are processed.  Creating the timer here
        ensures it is owned by the worker thread and fires correctly.
        '''
        self._pollTimer = QtCore.QTimer()
        self._pollTimer.setInterval(0)
        self._pollTimer.timeout.connect(self.poll)

    @QtCore.Slot()
    def startPolling(self) -> None:
        '''Start the continuous poll loop.

        Connect to this slot from the GUI thread via a signal; Qt will
        use a queued connection automatically so the timer is started
        in the correct thread.
        '''
        self._pollTimer.start()

    @QtCore.Slot()
    def stopPolling(self) -> None:
        '''Stop the continuous poll loop.

        Connect to this slot from the GUI thread via a signal; Qt will
        use a queued connection automatically.
        '''
        self._pollTimer.stop()

    def poll(self) -> None:
        '''Override to define continuous measurement behaviour.

        Called repeatedly in the worker thread while polling is active.
        Each call blocks in the worker thread (not the GUI thread) until
        the instrument responds.  Other queued events — such as
        ``set()`` calls from the GUI — are processed between calls.
        '''

    def close(self) -> None:
        '''Stop the poll loop and shut down the worker thread.

        Safe to call from the GUI thread.  Blocks until the worker
        thread has exited cleanly.  Any poll() call in progress will
        complete before the thread exits.
        '''
        self._thread.quit()
        self._thread.wait()


__all__ = ['QInstrumentWorker']
