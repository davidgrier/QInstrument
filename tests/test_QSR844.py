import pytest
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
