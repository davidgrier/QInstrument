import logging
import pytest
from instruments.Novanta.Opus532.fake import QFakeOpus532
from instruments.Novanta.Opus660.fake import QFakeOpus660
from instruments.Novanta.Opus1064.fake import QFakeOpus1064
from instruments.Novanta.Opus.instrument import QOpus
from instrument_contract import InstrumentContractTests


# ---------------------------------------------------------------------------
# Contract (exercised via Opus532 as the canonical concrete model)
# ---------------------------------------------------------------------------

class TestOpus532(InstrumentContractTests):

    fake_class = QFakeOpus532

    required_properties = {
        'power', 'maximum_power', 'wavelength', 'current',
        'emission', 'status', 'version',
        'laser_temperature', 'psu_temperature',
    }

    readonly_properties = {'status', 'version', 'laser_temperature', 'psu_temperature'}

    roundtrip_cases = [
        ('wavelength',      532.0),
        ('current',          50.0),
        ('emission',          True),
        ('maximum_power',  3000.0),
    ]


# ---------------------------------------------------------------------------
# Model-specific MAXIMUM_POWER defaults
# ---------------------------------------------------------------------------

class TestMaximumPowerDefaults:

    def test_opus532_maximum_power(self, qtbot):
        assert QFakeOpus532().get('maximum_power') == 6000.

    def test_opus660_maximum_power(self, qtbot):
        assert QFakeOpus660().get('maximum_power') == 1500.

    def test_opus1064_maximum_power(self, qtbot):
        assert QFakeOpus1064().get('maximum_power') == 10000.


# ---------------------------------------------------------------------------
# Power clamping to maximum_power
# ---------------------------------------------------------------------------

class TestPowerClamping:

    @pytest.fixture
    def laser(self, qtbot):
        return QFakeOpus532()

    def test_power_clamped_to_maximum_power(self, laser):
        laser.set('maximum_power', 100.)
        laser.set('power', 200.)
        assert laser.get('power') == 100.

    def test_power_not_clamped_below_maximum(self, laser):
        laser.set('maximum_power', 100.)
        laser.set('power', 50.)
        assert laser.get('power') == 50.

    def test_power_at_maximum_boundary(self, laser):
        laser.set('maximum_power', 100.)
        laser.set('power', 100.)
        assert laser.get('power') == 100.


# ---------------------------------------------------------------------------
# maximum_power validation (real instrument logic)
# ---------------------------------------------------------------------------

class TestMaximumPowerValidation:

    @pytest.fixture
    def laser(self, qtbot):
        f = QFakeOpus532()
        f._maximum_power = 1000.
        return f

    def test_zero_rejected(self, laser):
        QOpus._setMaximumPower(laser, 0.)
        assert laser._maximum_power == 1000.

    def test_negative_rejected(self, laser):
        QOpus._setMaximumPower(laser, -100.)
        assert laser._maximum_power == 1000.

    def test_valid_value_accepted(self, laser):
        QOpus._setMaximumPower(laser, 500.)
        assert laser._maximum_power == 500.

    def test_small_positive_accepted(self, laser):
        QOpus._setMaximumPower(laser, 0.1)
        assert laser._maximum_power == 0.1


# ---------------------------------------------------------------------------
# _getStatus (real instrument logic via monkeypatched receive)
# ---------------------------------------------------------------------------

class TestGetStatus:

    @pytest.fixture
    def laser(self, qtbot):
        return QFakeOpus532()

    def test_enabled_response_returns_true(self, laser, monkeypatch):
        monkeypatch.setattr(laser, 'receive', lambda **kw: 'ENABLED')
        assert QOpus._getStatus(laser) is True

    def test_disabled_response_returns_false(self, laser, monkeypatch):
        monkeypatch.setattr(laser, 'receive', lambda **kw: 'DISABLED')
        assert QOpus._getStatus(laser) is False

    def test_disabled_logs_warning(self, laser, monkeypatch, caplog):
        monkeypatch.setattr(laser, 'receive', lambda **kw: 'DISABLED')
        with caplog.at_level(logging.WARNING):
            QOpus._getStatus(laser)
        assert 'DISABLED' in caplog.text

    def test_unexpected_response_returns_false(self, laser, monkeypatch):
        monkeypatch.setattr(laser, 'receive', lambda **kw: 'STANDBY')
        assert QOpus._getStatus(laser) is False

    def test_fake_status_defaults_to_true(self, laser):
        assert laser.get('status') is True

    def test_status_is_readonly(self, laser):
        laser.set('status', False)
        assert laser.get('status') is True
