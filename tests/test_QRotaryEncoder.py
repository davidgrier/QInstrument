import pytest
from QInstrument.widgets.QRotaryEncoder import QRotaryEncoder


@pytest.fixture
def encoder(qtbot):
    widget = QRotaryEncoder(steps=10)
    qtbot.addWidget(widget)
    return widget


class TestSteps:

    def test_default_steps(self, qtbot):
        widget = QRotaryEncoder()
        qtbot.addWidget(widget)
        assert widget.steps() == 100
        assert widget.maximum() == 99

    def test_set_steps(self, encoder):
        encoder.setSteps(20)
        assert encoder.steps() == 20
        assert encoder.maximum() == 19

    def test_wrapping_is_on(self, encoder):
        assert encoder.wrapping()


class TestSignals:

    def test_turning_up_emits_step_up(self, encoder, qtbot):
        with qtbot.waitSignal(encoder.stepUp), \
                qtbot.assertNotEmitted(encoder.stepDown):
            encoder.setValue(1)

    def test_turning_down_emits_step_down(self, encoder, qtbot):
        encoder.setValue(5)
        with qtbot.waitSignal(encoder.stepDown), \
                qtbot.assertNotEmitted(encoder.stepUp):
            encoder.setValue(4)

    def test_wrap_around_forward_is_a_step_up(self, encoder, qtbot):
        encoder.setValue(9)
        with qtbot.waitSignal(encoder.stepUp):
            encoder.setValue(0)

    def test_wrap_around_backward_is_a_step_down(self, encoder, qtbot):
        with qtbot.waitSignal(encoder.stepDown):
            encoder.setValue(9)

    def test_the_same_value_emits_nothing(self, encoder, qtbot):
        with qtbot.assertNotEmitted(encoder.stepUp), \
                qtbot.assertNotEmitted(encoder.stepDown):
            encoder.setValue(0)
