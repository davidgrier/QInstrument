import pytest
from unittest.mock import patch
from instruments.StanfordResearch.SR830.fake import QFakeSR830
from instruments.StanfordResearch.SR830.instrument import QSR830
from instrument_contract import InstrumentContractTests


# ---------------------------------------------------------------------------
# Contract
# ---------------------------------------------------------------------------

class TestSR830(InstrumentContractTests):

    fake_class = QFakeSR830

    required_properties = {
        'amplitude', 'frequency', 'harmonic', 'internal_reference',
        'phase', 'reference_trigger',
        'dc_coupling', 'input_configuration', 'line_filter', 'shield_grounding',
        'dynamic_reserve', 'low_pass_slope', 'sensitivity',
        'synchronous_filter', 'time_constant',
    }

    readonly_properties = set()

    roundtrip_cases = [
        ('frequency',          1000.0),
        ('amplitude',             1.0),
        ('harmonic',                2),
        ('sensitivity',            10),
        ('time_constant',           5),
        ('internal_reference',   True),
        ('dc_coupling',         False),
        ('dynamic_reserve',         1),
    ]


# ---------------------------------------------------------------------------
# report()
# ---------------------------------------------------------------------------

class TestSR830Report:

    @pytest.fixture
    def sr830(self, qtbot):
        return QFakeSR830()

    def test_report_returns_three_values(self, sr830):
        assert len(sr830.report()) == 3

    def test_report_values_are_float(self, sr830):
        assert all(isinstance(v, float) for v in sr830.report())


# ---------------------------------------------------------------------------
# auto_offset() — channel validation
# ---------------------------------------------------------------------------

class TestSR830AutoOffset:

    @pytest.fixture
    def sr830(self, qtbot):
        return QFakeSR830()

    def test_valid_channels_do_not_raise(self, sr830):
        for ch in (1, 2, 3):
            QSR830.auto_offset(sr830, ch)

    def test_invalid_channel_zero_ignored(self, sr830):
        QSR830.auto_offset(sr830, 0)

    def test_invalid_channel_four_ignored(self, sr830):
        QSR830.auto_offset(sr830, 4)
