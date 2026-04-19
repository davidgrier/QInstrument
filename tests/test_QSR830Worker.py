import pytest
from qtpy import QtCore
from instruments.StanfordResearch.SR830.fake import QFakeSR830
from instruments.StanfordResearch.SR830.worker import QSR830Worker
from instruments.StanfordResearch.SR844.fake import QFakeSR844

pytestmark = pytest.mark.filterwarnings('ignore::DeprecationWarning')
from instruments.StanfordResearch.SR844.worker import QSR844Worker


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _start(worker):
    QtCore.QMetaObject.invokeMethod(
        worker, 'startPolling',
        QtCore.Qt.ConnectionType.QueuedConnection)


def _stop(worker):
    QtCore.QMetaObject.invokeMethod(
        worker, 'stopPolling',
        QtCore.Qt.ConnectionType.QueuedConnection)


# ---------------------------------------------------------------------------
# SR830Worker
# ---------------------------------------------------------------------------

class TestSR830Worker:

    @pytest.fixture
    def device(self, qtbot):
        return QFakeSR830()

    @pytest.fixture
    def worker(self, qtbot, device):
        w = QSR830Worker(device)
        yield w
        w.close()

    def test_measurement_signal_emitted(self, qtbot, worker):
        _start(worker)
        with qtbot.waitSignal(worker.measurement, timeout=1000):
            pass

    def test_measurement_has_three_elements(self, qtbot, worker):
        _start(worker)
        with qtbot.waitSignal(worker.measurement, timeout=1000) as blocker:
            pass
        assert len(blocker.args[0]) == 3

    def test_measurement_elements_are_floats(self, qtbot, worker):
        _start(worker)
        with qtbot.waitSignal(worker.measurement, timeout=1000) as blocker:
            pass
        assert all(isinstance(v, float) for v in blocker.args[0])

    def test_no_measurement_before_start(self, qtbot, worker):
        counts = []
        worker.measurement.connect(lambda _: counts.append(1))
        qtbot.wait(100)
        assert len(counts) == 0

    def test_measurement_stops_after_stop(self, qtbot, worker):
        _start(worker)
        with qtbot.waitSignal(worker.measurement, timeout=1000):
            pass
        _stop(worker)
        qtbot.wait(100)
        counts = []
        worker.measurement.connect(lambda _: counts.append(1))
        qtbot.wait(50)
        assert len(counts) == 0

    def test_instrument_in_worker_thread(self, qtbot, device, worker):
        qtbot.waitUntil(lambda: worker._thread.isRunning(), timeout=1000)
        assert device.thread() is worker._thread


# ---------------------------------------------------------------------------
# SR844Worker (structural parity)
# ---------------------------------------------------------------------------

class TestSR844Worker:

    @pytest.fixture
    def device(self, qtbot):
        return QFakeSR844()

    @pytest.fixture
    def worker(self, qtbot, device):
        w = QSR844Worker(device)
        yield w
        w.close()

    def test_measurement_signal_emitted(self, qtbot, worker):
        _start(worker)
        with qtbot.waitSignal(worker.measurement, timeout=1000):
            pass

    def test_measurement_has_three_elements(self, qtbot, worker):
        _start(worker)
        with qtbot.waitSignal(worker.measurement, timeout=1000) as blocker:
            pass
        assert len(blocker.args[0]) == 3
