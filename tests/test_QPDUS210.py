import pytest
from instruments.PiezoDrive.PDUS210.fake import QFakePDUS210
from instruments.PiezoDrive.PDUS210.instrument import QPDUS210
from instrument_contract import InstrumentContractTests


# ---------------------------------------------------------------------------
# Contract
# ---------------------------------------------------------------------------

class TestPDUS210(InstrumentContractTests):

    fake_class = QFakePDUS210

    required_properties = {
        'frequency', 'targetVoltage', 'maxFrequency', 'minFrequency',
        'targetPhase', 'maxLoadPower', 'targetPower', 'targetCurrent',
        'phaseGain', 'powerGain', 'currentGain',
        'phaseTracking', 'powerTracking', 'currentTracking',
        'frequencyWrapping', 'enabled',
        'phase', 'impedance', 'loadPower', 'amplifierPower',
        'current', 'temperature',
    }

    readonly_properties = {
        'phase', 'impedance', 'loadPower', 'amplifierPower',
        'current', 'temperature',
    }

    roundtrip_cases = [
        ('frequency',       42000.0),
        ('targetVoltage',        50),
        ('maxFrequency',      46000),
        ('minFrequency',      36000),
        ('targetPhase',          10),
        ('phaseGain',             3),
        ('phaseTracking',      True),
        ('enabled',            True),
    ]


# ---------------------------------------------------------------------------
# state() bulk read
# ---------------------------------------------------------------------------

class TestState:

    @pytest.fixture
    def pdus210(self, qtbot):
        return QFakePDUS210()

    def test_state_returns_dict(self, pdus210):
        assert isinstance(pdus210.state(), dict)

    def test_state_contains_motion_keys(self, pdus210):
        result = pdus210.state()
        for key in ('enabled', 'phaseTracking', 'powerTracking',
                    'currentTracking', 'frequency', 'temperature'):
            assert key in result, f'state() missing key {key!r}'

    def test_state_reflects_enabled(self, pdus210):
        pdus210.set('enabled', True)
        assert pdus210.state()['enabled'] is True

    def test_state_reflects_frequency(self, pdus210):
        pdus210.set('frequency', 42000.0)
        assert pdus210.state()['frequency'] == 42000.0

    def test_state_reflects_phase_tracking(self, pdus210):
        pdus210.set('phaseTracking', True)
        assert pdus210.state()['phaseTracking'] is True

    def test_save_returns_ok(self, pdus210):
        assert pdus210.save() == 'OK'


# ---------------------------------------------------------------------------
# _toggle() routing logic
# ---------------------------------------------------------------------------

class TestToggle:

    @pytest.fixture
    def pdus210(self, qtbot):
        return QFakePDUS210()

    def _capture(self, pdus210):
        '''Replace transmit with a list collector; return the list.'''
        sent = []
        pdus210.transmit = lambda data: sent.append(data)
        return sent

    def test_enable_transmits_enable(self, pdus210):
        sent = self._capture(pdus210)
        QPDUS210._toggle(pdus210, 'ENABLE', True)
        assert sent == ['ENABLE']

    def test_disable_transmits_disable(self, pdus210):
        sent = self._capture(pdus210)
        QPDUS210._toggle(pdus210, 'ENABLE', False)
        assert sent == ['DISABLE']

    def test_named_enable_uses_en_prefix(self, pdus210):
        sent = self._capture(pdus210)
        QPDUS210._toggle(pdus210, 'PHASE', True)
        assert sent == ['enPHASE']

    def test_named_disable_uses_dis_prefix(self, pdus210):
        sent = self._capture(pdus210)
        QPDUS210._toggle(pdus210, 'PHASE', False)
        assert sent == ['disPHASE']

    def test_power_tracking_enable(self, pdus210):
        sent = self._capture(pdus210)
        QPDUS210._toggle(pdus210, 'POWER', True)
        assert sent == ['enPOWER']

    def test_wrap_disable(self, pdus210):
        sent = self._capture(pdus210)
        QPDUS210._toggle(pdus210, 'WRAP', False)
        assert sent == ['disWRAP']
