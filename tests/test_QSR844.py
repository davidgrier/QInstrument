import pytest
from unittest.mock import patch
from instruments.StanfordResearch.SR844.fake import QFakeSR844
from instruments.StanfordResearch.SR844.instrument import QSR844
from instrument_contract import InstrumentContractTests


# ---------------------------------------------------------------------------
# Contract
# ---------------------------------------------------------------------------

class TestSR844(InstrumentContractTests):

    fake_class = QFakeSR844

    required_properties = {
        'frequency', 'harmonic', 'internal_reference', 'phase',
        'reference_impedance', 'input_impedance', 'wide_reserve',
        'close_reserve', 'low_pass_slope', 'sensitivity', 'time_constant',
        'reference_frequency', 'if_frequency',
        'x', 'y', 'r', 'theta',
    }

    readonly_properties = {'reference_frequency', 'if_frequency', 'x', 'y', 'r', 'theta'}

    roundtrip_cases = [
        ('frequency',          50e6),
        ('harmonic',              1),
        ('sensitivity',           5),
        ('time_constant',         4),
        ('internal_reference', True),
        ('wide_reserve',          1),
        ('close_reserve',         2),
        ('reference_impedance',   1),
    ]


# ---------------------------------------------------------------------------
# report()
# ---------------------------------------------------------------------------

class TestSR844Report:

    @pytest.fixture
    def sr844(self, qtbot):
        return QFakeSR844()

    def test_report_returns_three_values(self, sr844):
        assert len(sr844.report()) == 3

    def test_report_values_are_float(self, sr844):
        assert all(isinstance(v, float) for v in sr844.report())


# ---------------------------------------------------------------------------
# auto_offset() — channel validation
# ---------------------------------------------------------------------------

class TestSR844AutoOffset:

    @pytest.fixture
    def sr844(self, qtbot):
        return QFakeSR844()

    def test_valid_channels_do_not_raise(self, sr844):
        for ch in (1, 2, 3):
            QSR844.auto_offset(sr844, ch)

    def test_invalid_channel_zero_ignored(self, sr844):
        QSR844.auto_offset(sr844, 0)

    def test_invalid_channel_four_ignored(self, sr844):
        QSR844.auto_offset(sr844, 4)


# ---------------------------------------------------------------------------
# _poll() — batched SNAP output
# ---------------------------------------------------------------------------

class TestSR844Poll:

    @pytest.fixture
    def sr844(self, qtbot):
        return QFakeSR844()

    def test_poll_emits_frequency_r_theta(self, sr844):
        sr844._polling = True
        received = {}
        sr844.propertyValue.connect(lambda n, v: received.update({n: v}))
        with patch.object(sr844, 'report', return_value=[50e6, 0.3, 30.0]), \
             patch('qtpy.QtCore.QTimer.singleShot'):
            sr844._poll()
        assert received.get('frequency') == pytest.approx(50e6)
        assert received.get('r') == pytest.approx(0.3)
        assert received.get('theta') == pytest.approx(30.0)

    def test_poll_does_not_emit_when_stopped(self, sr844):
        sr844._polling = False
        received = []
        sr844.propertyValue.connect(lambda n, v: received.append(n))
        with patch.object(sr844, 'report') as mock_report:
            sr844._poll()
        mock_report.assert_not_called()
        assert received == []

    def test_poll_schedules_next_call(self, sr844):
        sr844._polling = True
        with patch.object(sr844, 'report', return_value=[0., 0., 0.]), \
             patch('qtpy.QtCore.QTimer.singleShot') as mock_shot:
            sr844._poll()
        mock_shot.assert_called_once_with(sr844.POLL_INTERVAL, sr844._poll)
