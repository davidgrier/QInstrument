import pytest
from instruments.IPGPhotonics.IPGLaser.fake import QFakeIPGLaser
from instruments.IPGPhotonics.IPGLaser.instrument import QIPGLaser
from instrument_contract import InstrumentContractTests


# ---------------------------------------------------------------------------
# Contract
# ---------------------------------------------------------------------------

class TestIPGLaser(InstrumentContractTests):

    fake_class = QFakeIPGLaser

    required_properties = {
        'current', 'maximum_current', 'aiming', 'emission',
        'power', 'power_supply', 'keyswitch', 'fault',
        'minimum_current', 'firmware', 'temperature',
    }

    readonly_properties = {
        'power', 'power_supply', 'keyswitch', 'fault',
        'minimum_current', 'firmware', 'temperature',
    }

    roundtrip_cases = [
        ('current',          50.0),
        ('maximum_current',  80.0),
        ('aiming',           True),
        ('emission',         True),
    ]


# ---------------------------------------------------------------------------
# Current clamping to maximum_current
# ---------------------------------------------------------------------------

class TestCurrentClamping:

    @pytest.fixture
    def laser(self, qtbot):
        return QFakeIPGLaser()

    def test_current_clamped_to_maximum_current(self, laser):
        laser.set('maximum_current', 50.)
        laser.set('current', 80.)
        assert laser.get('current') == 50.

    def test_current_not_clamped_below_maximum(self, laser):
        laser.set('maximum_current', 80.)
        laser.set('current', 50.)
        assert laser.get('current') == 50.

    def test_current_at_maximum_boundary(self, laser):
        laser.set('maximum_current', 60.)
        laser.set('current', 60.)
        assert laser.get('current') == 60.


# ---------------------------------------------------------------------------
# maximum_current validation (real instrument logic)
# ---------------------------------------------------------------------------

class TestMaximumCurrentValidation:

    @pytest.fixture
    def laser(self, qtbot):
        f = QFakeIPGLaser()
        f._maximum_current = 80.
        return f

    def test_value_above_100_rejected(self, laser):
        QIPGLaser._setMaximumCurrent(laser, 150.)
        assert laser._maximum_current == 80.

    def test_negative_value_rejected(self, laser):
        QIPGLaser._setMaximumCurrent(laser, -5.)
        assert laser._maximum_current == 80.

    def test_zero_accepted(self, laser):
        QIPGLaser._setMaximumCurrent(laser, 0.)
        assert laser._maximum_current == 0.

    def test_hundred_accepted(self, laser):
        QIPGLaser._setMaximumCurrent(laser, 100.)
        assert laser._maximum_current == 100.

    def test_valid_mid_range_accepted(self, laser):
        QIPGLaser._setMaximumCurrent(laser, 60.)
        assert laser._maximum_current == 60.


# ---------------------------------------------------------------------------
# status() snapshot
# ---------------------------------------------------------------------------

class TestStatus:

    @pytest.fixture
    def laser(self, qtbot):
        return QFakeIPGLaser()

    def test_status_contains_expected_keys(self, laser):
        assert set(laser.status().keys()) == {
            'power_supply', 'keyswitch', 'aiming', 'emission', 'fault', 'power'}

    def test_status_default_power_supply_on(self, laser):
        assert laser.status()['power_supply'] is True

    def test_status_default_keyswitch_on(self, laser):
        assert laser.status()['keyswitch'] is True

    def test_status_default_emission_off(self, laser):
        assert laser.status()['emission'] is False

    def test_status_default_fault_clear(self, laser):
        assert laser.status()['fault'] is False

    def test_status_default_power_zero(self, laser):
        assert laser.status()['power'] == 0.


# ---------------------------------------------------------------------------
# fault_detail() bitmask decoding
# ---------------------------------------------------------------------------

class TestFaultDetail:

    @pytest.fixture
    def laser(self, qtbot):
        return QFakeIPGLaser()

    def test_no_faults_returns_empty_list(self, laser):
        laser._flags = lambda: 0
        assert QIPGLaser.fault_detail(laser) == []

    def test_over_temperature_detected(self, laser):
        laser._flags = lambda: QIPGLaser.flag['TMP']
        assert QIPGLaser.fault_detail(laser) == ['over-temperature']

    def test_backreflection_detected(self, laser):
        laser._flags = lambda: QIPGLaser.flag['BKR']
        assert QIPGLaser.fault_detail(laser) == ['excessive backreflection']

    def test_power_supply_off_detected(self, laser):
        laser._flags = lambda: QIPGLaser.flag['PWR']
        assert QIPGLaser.fault_detail(laser) == ['power supply off']

    def test_unexpected_emission_detected(self, laser):
        laser._flags = lambda: QIPGLaser.flag['UNX']
        assert QIPGLaser.fault_detail(laser) == ['unexpected emission']

    def test_multiple_faults_all_reported(self, laser):
        laser._flags = lambda: QIPGLaser.flag['TMP'] | QIPGLaser.flag['PWR']
        result = QIPGLaser.fault_detail(laser)
        assert 'over-temperature' in result
        assert 'power supply off' in result
        assert len(result) == 2

    def test_all_four_faults_reported(self, laser):
        all_faults = (QIPGLaser.flag['TMP'] | QIPGLaser.flag['BKR'] |
                      QIPGLaser.flag['PWR'] | QIPGLaser.flag['UNX'])
        laser._flags = lambda: all_faults
        assert len(QIPGLaser.fault_detail(laser)) == 4
