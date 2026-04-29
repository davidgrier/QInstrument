import pytest
from unittest.mock import patch, call
from qtpy import QtCore

from lib.QAbstractInstrument import QAbstractInstrument
from lib.QPollingMixin import QPollingMixin


class PollingInstrument(QPollingMixin, QAbstractInstrument):
    '''Minimal concrete instrument with default poll loop.'''


class CustomPollInstrument(QPollingMixin, QAbstractInstrument):
    '''Instrument with a custom _poll override.'''

    poll_count = 0

    def _poll(self) -> None:
        if not getattr(self, '_polling', False):
            return
        self.poll_count += 1
        if getattr(self, '_polling', False):
            QtCore.QTimer.singleShot(self.POLL_INTERVAL, self._poll)


@pytest.fixture
def inst(qtbot):
    return PollingInstrument()


@pytest.fixture
def custom(qtbot):
    return CustomPollInstrument()


# ---------------------------------------------------------------------------
# startPolling / stopPolling
# ---------------------------------------------------------------------------

class TestPollingControl:

    def test_start_sets_polling_flag(self, inst):
        with patch.object(inst, '_poll'):
            inst.startPolling()
        assert inst._polling is True

    def test_start_calls_poll(self, inst):
        with patch.object(inst, '_poll') as mock_poll:
            inst.startPolling()
        mock_poll.assert_called_once()

    def test_stop_clears_polling_flag(self, inst):
        inst._polling = True
        inst.stopPolling()
        assert inst._polling is False

    def test_stop_before_start_is_safe(self, inst):
        inst.stopPolling()
        assert inst._polling is False

    def test_polling_flag_absent_before_start(self, inst):
        assert not getattr(inst, '_polling', False)


# ---------------------------------------------------------------------------
# Default _poll behaviour
# ---------------------------------------------------------------------------

class TestDefaultPoll:

    def test_poll_calls_get_for_each_property(self, inst):
        inst.registerProperty('a', getter=lambda: 1.0, setter=None,
                              ptype=float)
        inst.registerProperty('b', getter=lambda: 2.0, setter=None,
                              ptype=float)
        inst._polling = True
        received = {}
        inst.propertyValue.connect(lambda n, v: received.update({n: v}))
        with patch('qtpy.QtCore.QTimer.singleShot'):
            inst._poll()
        assert 'a' in received
        assert 'b' in received

    def test_poll_schedules_next_call_when_polling(self, inst):
        inst._polling = True
        with patch('qtpy.QtCore.QTimer.singleShot') as mock_shot:
            inst._poll()
        mock_shot.assert_called_once_with(inst.POLL_INTERVAL, inst._poll)

    def test_poll_does_not_reschedule_when_stopped(self, inst):
        inst._polling = False
        with patch('qtpy.QtCore.QTimer.singleShot') as mock_shot:
            inst._poll()
        mock_shot.assert_not_called()

    def test_poll_exits_immediately_if_not_polling(self, inst):
        inst.registerProperty('a', getter=lambda: 1.0, setter=None,
                              ptype=float)
        received = []
        inst.propertyValue.connect(lambda n, v: received.append(n))
        inst._poll()
        assert received == []


# ---------------------------------------------------------------------------
# Custom _poll override
# ---------------------------------------------------------------------------

class TestCustomPoll:

    def test_custom_poll_is_called(self, custom):
        with patch('qtpy.QtCore.QTimer.singleShot'):
            custom._polling = True
            custom._poll()
        assert custom.poll_count == 1

    def test_custom_poll_does_not_call_default(self, custom):
        with patch.object(QPollingMixin, '_poll') as base_poll:
            with patch('qtpy.QtCore.QTimer.singleShot'):
                custom._polling = True
                custom._poll()
        base_poll.assert_not_called()


# ---------------------------------------------------------------------------
# POLL_INTERVAL default
# ---------------------------------------------------------------------------

class TestPollInterval:

    def test_default_poll_interval_is_zero(self, inst):
        assert inst.POLL_INTERVAL == 0
