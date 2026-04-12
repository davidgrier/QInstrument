import pytest
from instruments.PriorScientific.Proscan.fake import QFakeProscan
from instruments.PriorScientific.Proscan.instrument import QProscan


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def proscan(qtbot):
    return QFakeProscan()


# ---------------------------------------------------------------------------
# _parse_limits — bitmask decoding
# ---------------------------------------------------------------------------

class TestParseLimits:
    '''_parse_limits() converts a raw byte to a per-axis tuple or None.'''

    def test_zero_returns_none(self, proscan):
        assert proscan._parse_limits(0) is None

    def test_x_positive_bit(self, proscan):
        assert proscan._parse_limits(0x01) == (True, False, False, False)

    def test_x_negative_bit(self, proscan):
        assert proscan._parse_limits(0x02) == (True, False, False, False)

    def test_x_both_bits(self, proscan):
        assert proscan._parse_limits(0x03) == (True, False, False, False)

    def test_y_positive_bit(self, proscan):
        assert proscan._parse_limits(0x04) == (False, True, False, False)

    def test_y_negative_bit(self, proscan):
        assert proscan._parse_limits(0x08) == (False, True, False, False)

    def test_y_both_bits(self, proscan):
        assert proscan._parse_limits(0x0C) == (False, True, False, False)

    def test_z_positive_bit(self, proscan):
        assert proscan._parse_limits(0x10) == (False, False, True, False)

    def test_z_negative_bit(self, proscan):
        assert proscan._parse_limits(0x20) == (False, False, True, False)

    def test_z_both_bits(self, proscan):
        assert proscan._parse_limits(0x30) == (False, False, True, False)

    def test_fourth_positive_bit(self, proscan):
        assert proscan._parse_limits(0x40) == (False, False, False, True)

    def test_fourth_negative_bit(self, proscan):
        assert proscan._parse_limits(0x80) == (False, False, False, True)

    def test_fourth_both_bits(self, proscan):
        assert proscan._parse_limits(0xC0) == (False, False, False, True)

    def test_xy_axes(self, proscan):
        assert proscan._parse_limits(0x05) == (True, True, False, False)

    def test_xz_axes(self, proscan):
        assert proscan._parse_limits(0x11) == (True, False, True, False)

    def test_yz_axes(self, proscan):
        assert proscan._parse_limits(0x14) == (False, True, True, False)

    def test_all_axes(self, proscan):
        assert proscan._parse_limits(0xFF) == (True, True, True, True)


# ---------------------------------------------------------------------------
# Limit methods on the fake
# ---------------------------------------------------------------------------

class TestLimitMethods:

    def test_active_limits_returns_none(self, proscan):
        assert proscan.active_limits() is None

    def test_triggered_limits_returns_none(self, proscan):
        assert proscan.triggered_limits() is None

    def test_limits_property_returns_none(self, proscan):
        assert proscan.get('limits') is None

    def test_limits_property_is_readonly(self, proscan):
        proscan.set('limits', (True, False, False, False))
        assert proscan.get('limits') is None


# ---------------------------------------------------------------------------
# Motion guard on set_position()
# ---------------------------------------------------------------------------

class TestSetPositionGuard:

    def test_blocked_when_moving(self, proscan):
        '''set_position() must return False and not transmit when moving.'''
        proscan.status = lambda: 0x01
        sent = []
        proscan.expect = lambda *args: sent.append(args) or True
        result = QProscan.set_position(proscan, [100, 200, 0])
        assert result is False
        assert sent == []

    def test_blocked_on_any_motion_bit(self, proscan):
        '''All four motion bits (0–3) trigger the guard.'''
        for bit in (0x1, 0x2, 0x4, 0x8):
            proscan.status = lambda b=bit: b
            result = QProscan.set_position(proscan, [0, 0, 0])
            assert result is False, f'guard failed for motion bit 0x{bit:02X}'

    def test_allowed_when_not_moving(self, proscan):
        '''set_position() proceeds and returns expect() result when idle.'''
        proscan.status = lambda: 0
        proscan.expect = lambda *args: True
        result = QProscan.set_position(proscan, [100, 200, 0])
        assert result is True


# ---------------------------------------------------------------------------
# Properties
# ---------------------------------------------------------------------------

class TestProperties:

    def test_required_properties_registered(self, proscan):
        expected = {'speed', 'acceleration', 'scurve',
                    'zspeed', 'zacceleration', 'zscurve',
                    'stepsize', 'zstepsize', 'resolution',
                    'flip', 'mirror', 'moving', 'limits'}
        assert expected.issubset(set(proscan.properties))

    def test_moving_is_readonly(self, proscan):
        proscan.set('moving', True)
        assert proscan.get('moving') is False

    def test_speed_roundtrip(self, proscan):
        proscan.set('speed', 75)
        assert proscan.get('speed') == 75

    def test_flip_roundtrip(self, proscan):
        proscan.set('flip', True)
        assert proscan.get('flip') is True

    def test_stepsize_roundtrip(self, proscan):
        proscan.set('stepsize', 2.5)
        assert proscan.get('stepsize') == 2.5


# ---------------------------------------------------------------------------
# Basic fake behaviour
# ---------------------------------------------------------------------------

class TestFakeBehaviour:

    def test_identify_returns_true(self, proscan):
        assert proscan.identify() is True

    def test_is_open(self, proscan):
        assert proscan.isOpen() is True

    def test_emergency_stop_returns_true(self, proscan):
        assert proscan.emergency_stop() is True

    def test_position_returns_origin(self, proscan):
        assert proscan.position() == [0, 0, 0]

    def test_stop_returns_true(self, proscan):
        assert proscan.stop() is True
