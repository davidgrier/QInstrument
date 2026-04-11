import pytest
from qtpy import QtCore
from widgets.QLedWidget import QLedWidget


@pytest.fixture
def led(qtbot):
    w = QLedWidget()
    qtbot.addWidget(w)
    return w


# ---------------------------------------------------------------------------
# Initial state
# ---------------------------------------------------------------------------

class TestInit:

    def test_default_color_is_red(self, led):
        assert led.color == QLedWidget.RED

    def test_default_state_is_on(self, led):
        assert led.state == QLedWidget.ON

    def test_default_blink_is_false(self, led):
        assert led.blink is False

    def test_default_interval_is_400(self, led):
        assert led.interval == 400

    def test_custom_color(self, qtbot):
        w = QLedWidget(color=QLedWidget.GREEN)
        qtbot.addWidget(w)
        assert w.color == QLedWidget.GREEN

    def test_custom_state(self, qtbot):
        w = QLedWidget(state=QLedWidget.OFF)
        qtbot.addWidget(w)
        assert w.state == QLedWidget.OFF


# ---------------------------------------------------------------------------
# value / setValue
# ---------------------------------------------------------------------------

class TestValue:

    def test_value_true_when_on(self, led):
        led.state = QLedWidget.ON
        assert led.value() is True

    def test_value_false_when_off(self, led):
        led.state = QLedWidget.OFF
        assert led.value() is False

    def test_set_value_true_turns_on(self, led):
        led.state = QLedWidget.OFF
        led.setValue(True)
        assert led.state == QLedWidget.ON

    def test_set_value_false_turns_off(self, led):
        led.state = QLedWidget.ON
        led.setValue(False)
        assert led.state == QLedWidget.OFF


# ---------------------------------------------------------------------------
# flipState
# ---------------------------------------------------------------------------

class TestFlipState:

    def test_flip_on_to_off(self, led):
        led.state = QLedWidget.ON
        led.flipState()
        assert led.state == QLedWidget.OFF

    def test_flip_off_to_on(self, led):
        led.state = QLedWidget.OFF
        led.flipState()
        assert led.state == QLedWidget.ON


# ---------------------------------------------------------------------------
# blink
# ---------------------------------------------------------------------------

class TestBlink:

    def test_blink_starts_timer(self, led):
        led.blink = True
        assert led.timer.isActive()

    def test_blink_false_stops_timer(self, led):
        led.blink = True
        led.blink = False
        assert not led.timer.isActive()

    def test_blink_restores_saved_state(self, led):
        led.state = QLedWidget.OFF
        led.blink = True
        led.flipState()           # manually flip while blinking
        led.blink = False
        assert led.state == QLedWidget.OFF   # restored to state before blink

    def test_interval_setter_restarts_active_timer(self, led):
        led.blink = True
        led.interval = 200
        assert led.timer.isActive()
        assert led.interval == 200


# ---------------------------------------------------------------------------
# Color class attributes
# ---------------------------------------------------------------------------

class TestColorAliases:

    def test_all_colors_accessible(self):
        for color in (QLedWidget.RED, QLedWidget.AMBER, QLedWidget.GREEN,
                      QLedWidget.BLUE, QLedWidget.VIOLET, QLedWidget.WHITE):
            assert isinstance(color, QLedWidget.Color)

    def test_hexcodes_defined_for_all_colors(self):
        for color in QLedWidget.Color:
            assert color in QLedWidget.hexcodes
            assert QLedWidget.ON in QLedWidget.hexcodes[color]
            assert QLedWidget.OFF in QLedWidget.hexcodes[color]
