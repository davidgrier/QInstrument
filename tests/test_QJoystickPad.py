import numpy as np
import pytest
from qtpy import QtGui
from QInstrument.widgets.QJoystickPad import QJoystickPad


@pytest.fixture
def pad(qtbot):
    widget = QJoystickPad()
    qtbot.addWidget(widget)
    widget.resize(240, 240)
    widget.show()
    return widget


class TestProperties:

    def test_defaults(self, pad):
        assert pad.stepFraction == 0.25
        assert pad.holdThreshold == 300

    def test_step_fraction(self, pad):
        pad.setStepFraction(0.5)
        assert pad.stepFraction == 0.5

    def test_hold_threshold(self, pad):
        pad.setHoldThreshold(50)
        assert pad.holdThreshold == 50

    def test_range_proxies_the_joystick(self, pad):
        pad.setRange(0., 4.)
        assert (pad.minimum(), pad.maximum()) == (0., 4.)
        assert (pad.joystick.minimum(), pad.joystick.maximum()) == (0., 4.)

    def test_fullscale(self, pad):
        pad.fullscale = 2.
        assert (pad.minimum(), pad.maximum()) == (-2., 2.)

    def test_colors_reach_the_joystick_and_buttons(self, pad):
        pad.setPadColor(QtGui.QColor('#102030'))
        pad.setKnobColor(QtGui.QColor('#405060'))
        assert pad.joystick.padColor == QtGui.QColor('#102030')
        assert pad.joystick.knobColor == QtGui.QColor('#405060')
        assert all(b.color == QtGui.QColor('#102030')
                   for b in pad._buttons.values())


class TestClick:

    @pytest.mark.parametrize('direction', ['up', 'down', 'left', 'right'])
    def test_a_click_emits_stepped(self, pad, qtbot, direction):
        with qtbot.waitSignal(pad.stepped) as blocker:
            pad._buttons[direction].click()
        assert blocker.args == [direction]

    def test_a_click_moves_the_knob_then_returns_it(self, pad, qtbot):
        pad._buttons['right'].click()
        assert pad.joystick.active
        qtbot.waitUntil(lambda: not pad.joystick.active, timeout=1000)


class TestHold:

    def test_a_hold_emits_velocity_and_release_emits_zero(self, pad, qtbot):
        pad.setHoldThreshold(10)
        pad.setRange(-1., 1.)
        button = pad._buttons['right']
        with qtbot.waitSignal(pad.positionChanged, timeout=1000) as blocker:
            button.pressed.emit()
        # a quarter of full scale to the right: lo + (0.25 + 1) / 2 * (hi - lo)
        assert blocker.args[0][0] == pytest.approx(0.25)
        with qtbot.waitSignal(pad.positionChanged) as blocker:
            button.released.emit()
        assert np.allclose(blocker.args[0], 0.)

    def test_the_click_after_a_hold_is_suppressed(self, pad, qtbot):
        pad.setHoldThreshold(10)
        button = pad._buttons['up']
        with qtbot.waitSignal(pad.positionChanged, timeout=1000):
            button.pressed.emit()
        button.released.emit()
        with qtbot.assertNotEmitted(pad.stepped):
            pad._onClicked('up')

    def test_release_before_the_threshold_is_not_a_hold(self, pad, qtbot):
        pad.setHoldThreshold(5000)
        button = pad._buttons['left']
        with qtbot.assertNotEmitted(pad.positionChanged):
            button.pressed.emit()
            button.released.emit()


class TestForwarding:

    def test_joystick_motion_is_forwarded(self, pad, qtbot):
        with qtbot.waitSignal(pad.positionChanged):
            pad.joystick.positionChanged.emit(np.array([0.5, 0.5]))


class TestLayout:

    def test_height_for_width(self, pad):
        assert pad.hasHeightForWidth()
        assert pad.heightForWidth(200) >= 200

    def test_size_hints(self, pad):
        assert pad.sizeHint().width() > 0
        assert pad.minimumSizeHint().width() > 0

    def test_renders(self, pad):
        assert not pad.grab().toImage().isNull()
