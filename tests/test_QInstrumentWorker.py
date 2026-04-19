import pytest
from qtpy import QtCore
from lib.QFakeInstrument import QFakeInstrument
from lib.QInstrumentWorker import QInstrumentWorker

pytestmark = pytest.mark.filterwarnings('ignore::DeprecationWarning')


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _CountingWorker(QInstrumentWorker):
    '''Worker that emits a signal on every poll tick.'''
    polled = QtCore.Signal()

    def poll(self) -> None:
        self.polled.emit()


class _SetReadWorker(QInstrumentWorker):
    '''Worker that calls get() once per tick and emits the result.'''
    read = QtCore.Signal(object)

    def poll(self) -> None:
        self.stopPolling()
        value = self.instrument.get('frequency')
        self.read.emit(value)


class _FakeWithFrequency(QFakeInstrument):
    def _registerProperties(self):
        self._register('frequency', 'FREQ', float)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def device(qtbot):
    return _FakeWithFrequency()


@pytest.fixture
def worker(qtbot, device):
    w = _CountingWorker(device)
    yield w
    w.close()


# ---------------------------------------------------------------------------
# Thread lifecycle
# ---------------------------------------------------------------------------

class TestThreadLifecycle:

    def test_thread_starts_on_construction(self, qtbot, device):
        w = _CountingWorker(device)
        qtbot.waitUntil(lambda: w._thread.isRunning(), timeout=1000)
        w.close()

    def test_instrument_in_worker_thread(self, qtbot, device):
        w = _CountingWorker(device)
        qtbot.waitUntil(lambda: w._thread.isRunning(), timeout=1000)
        assert device.thread() is w._thread
        w.close()

    def test_worker_in_worker_thread(self, qtbot, device):
        w = _CountingWorker(device)
        qtbot.waitUntil(lambda: w._thread.isRunning(), timeout=1000)
        assert w.thread() is w._thread
        w.close()

    def test_close_stops_thread(self, qtbot, device):
        w = _CountingWorker(device)
        qtbot.waitUntil(lambda: w._thread.isRunning(), timeout=1000)
        w.close()
        assert not w._thread.isRunning()

    def test_instrument_property_accessible(self, worker, device):
        assert worker.instrument is device


# ---------------------------------------------------------------------------
# Poll loop
# ---------------------------------------------------------------------------

class TestPollLoop:

    def _start(self, worker):
        QtCore.QMetaObject.invokeMethod(
            worker, 'startPolling',
            QtCore.Qt.ConnectionType.QueuedConnection)

    def _stop(self, worker):
        QtCore.QMetaObject.invokeMethod(
            worker, 'stopPolling',
            QtCore.Qt.ConnectionType.QueuedConnection)

    def test_poll_called_after_startPolling(self, qtbot, worker):
        self._start(worker)
        with qtbot.waitSignal(worker.polled, timeout=1000):
            pass

    def test_poll_not_called_before_startPolling(self, qtbot, worker):
        counts = []
        worker.polled.connect(lambda: counts.append(1))
        qtbot.wait(100)
        assert len(counts) == 0

    def test_poll_stops_after_stopPolling(self, qtbot, worker):
        self._start(worker)
        with qtbot.waitSignal(worker.polled, timeout=1000):
            pass
        self._stop(worker)
        qtbot.wait(100)
        counts = []
        worker.polled.connect(lambda: counts.append(1))
        qtbot.wait(50)
        assert len(counts) == 0

    def test_poll_restartable(self, qtbot, worker):
        '''Polling can be stopped and restarted.'''
        self._start(worker)
        with qtbot.waitSignal(worker.polled, timeout=1000):
            pass
        self._stop(worker)
        qtbot.wait(50)
        self._start(worker)
        with qtbot.waitSignal(worker.polled, timeout=1000):
            pass


# ---------------------------------------------------------------------------
# Cross-thread instrument access
# ---------------------------------------------------------------------------

class TestCrossThreadAccess:

    def test_set_from_gui_reaches_instrument(self, qtbot, device):
        '''A set() call queued from the GUI thread updates the instrument.'''
        w = _SetReadWorker(device)
        # set() from the GUI thread via signal (auto-queued to worker thread)
        device.set('frequency', 500.0)
        with qtbot.waitSignal(w.read, timeout=1000) as blocker:
            QtCore.QMetaObject.invokeMethod(
                w, 'startPolling',
                QtCore.Qt.ConnectionType.QueuedConnection)
        assert blocker.args[0] == 500.0
        w.close()

    def test_propertyValue_signal_reaches_gui(self, qtbot, device):
        '''propertyValue emitted in the worker thread arrives in the GUI.'''
        w = QInstrumentWorker(device)
        qtbot.waitUntil(lambda: w._thread.isRunning(), timeout=1000)
        with qtbot.waitSignal(device.propertyValue, timeout=1000) as blocker:
            QtCore.QMetaObject.invokeMethod(
                device, 'set',
                QtCore.Qt.ConnectionType.QueuedConnection,
                QtCore.Q_ARG(str, 'frequency'),
                QtCore.Q_ARG(object, 250.0))
        assert blocker.args[0] == 'frequency'
        w.close()
