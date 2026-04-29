from __future__ import annotations

import logging
import warnings
from qtpy import QtCore

logger = logging.getLogger(__name__)


class QInstrumentWorker(QtCore.QObject):
    '''Deprecated. Runs a QAbstractInstrument in a dedicated QThread.

    .. deprecated::
        :class:`QInstrumentWidget` now moves every :class:`QSerialInstrument`
        into a worker thread automatically on first show.  There is no longer
        any need to manage a separate worker.

    Subclass and override :meth:`poll` to define continuous measurement
    behavior.  Connect :meth:`startPolling` and :meth:`stopPolling` via
    signals from the widget.

    Parameters
    ----------
    instrument : QAbstractInstrument
        Instrument to run in the worker thread.

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
            'release. QInstrumentWidget now moves QSerialInstrument instances '
            'into a worker thread automatically.',
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
