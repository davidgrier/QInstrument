import pytest
from instruments.StanfordResearch.DS345.fake import QFakeDS345
from instruments.StanfordResearch.DS345.instrument import QDS345
from instrument_contract import InstrumentContractTests


# ---------------------------------------------------------------------------
# Contract
# ---------------------------------------------------------------------------

class TestDS345(InstrumentContractTests):

    fake_class = QFakeDS345

    required_properties = {
        'amplitude', 'mute', 'frequency', 'offset', 'phase',
        'sampling_frequency', 'waveform', 'invert',
        'modulation', 'modulation_type', 'modulation_waveform',
        'modulation_rate', 'burst_count', 'am_depth', 'fm_span', 'pm_span',
        'sweep_span', 'sweep_center_frequency',
        'sweep_start_frequency', 'sweep_stop_frequency',
        'trigger_rate', 'trigger_source',
    }

    readonly_properties = set()

    roundtrip_cases = [
        ('frequency',      1000.0),
        ('offset',            0.5),
        ('phase',            45.0),
        ('waveform',            2),
        ('invert',           True),
        ('burst_count',        10),
        ('trigger_source',      1),
        ('modulation_type',     2),
    ]


# ---------------------------------------------------------------------------
# Mute — save / restore amplitude
# ---------------------------------------------------------------------------

class TestMute:

    @pytest.fixture
    def ds345(self, qtbot):
        return QFakeDS345()

    def test_mute_sets_amplitude_to_zero(self, ds345):
        ds345.set('amplitude', 2.0)
        ds345.set('mute', True)
        assert ds345.get('amplitude') == 0.0

    def test_unmute_restores_amplitude(self, ds345):
        ds345.set('amplitude', 2.0)
        ds345.set('mute', True)
        ds345.set('mute', False)
        assert ds345.get('amplitude') == 2.0

    def test_mute_is_idempotent(self, ds345):
        '''Second mute must not overwrite the saved amplitude.'''
        ds345.set('amplitude', 1.5)
        ds345.set('mute', True)
        ds345.set('mute', True)
        ds345.set('mute', False)
        assert ds345.get('amplitude') == 1.5

    def test_unmute_is_idempotent(self, ds345):
        '''Unmuting when already unmuted must leave amplitude unchanged.'''
        ds345.set('amplitude', 1.0)
        ds345.set('mute', False)
        assert ds345.get('amplitude') == 1.0

    def test_mute_status_roundtrip(self, ds345):
        assert ds345.get('mute') is False
        ds345.set('mute', True)
        assert ds345.get('mute') is True
        ds345.set('mute', False)
        assert ds345.get('mute') is False
