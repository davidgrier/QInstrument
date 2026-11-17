import numpy as np
import pytest
from qtpy import QtCore, QtGui
from QInstrument.widgets.QJoystick import QJoystick


@pytest.fixture
def stick(qtbot):
    widget = QJoystick()
    qtbot.addWidget(widget)
    widget.resize(200, 200)
    widget.show()
    return widget


def press(widget, point):
    QtCore.QCoreApplication.sendEvent(
        widget, QtGui.QMouseEvent(
            QtCore.QEvent.Type.MouseButtonPress, QtCore.QPointF(point),
            QtCore.Qt.MouseButton.LeftButton,
            QtCore.Qt.MouseButton.LeftButton,
            QtCore.Qt.KeyboardModifier.NoModifier))


def move(widget, point):
    QtCore.QCoreApplication.sendEvent(
        widget, QtGui.QMouseEvent(
            QtCore.QEvent.Type.MouseMove, QtCore.QPointF(point),
            QtCore.Qt.MouseButton.NoButton,
            QtCore.Qt.MouseButton.LeftButton,
            QtCore.Qt.KeyboardModifier.NoModifier))


def release(widget, point):
    QtCore.QCoreApplication.sendEvent(
        widget, QtGui.QMouseEvent(
            QtCore.QEvent.Type.MouseButtonRelease, QtCore.QPointF(point),
            QtCore.Qt.MouseButton.LeftButton,
            QtCore.Qt.MouseButton.NoButton,
            QtCore.Qt.KeyboardModifier.NoModifier))


class TestRange:

    def test_default_range_is_unit(self, stick):
        assert (stick.minimum(), stick.maximum()) == (-1., 1.)

    def test_fullscale_sets_a_symmetric_range(self, stick):
        stick.fullscale = 5.
        assert (stick.minimum(), stick.maximum()) == (-5., 5.)
        assert stick.fullscale == 5.

    def test_constructor_fullscale(self, qtbot):
        widget = QJoystick(fullscale=3.)
        qtbot.addWidget(widget)
        assert (widget.minimum(), widget.maximum()) == (-3., 3.)

    def test_set_range(self, stick):
        stick.setRange(0., 10.)
        assert (stick.minimum(), stick.maximum()) == (0., 10.)


class TestGeometry:

    def test_resize_sets_radius_and_limit(self, stick):
        assert stick.radius == pytest.approx(100 * (1 - stick.padding))
        assert stick.limit == pytest.approx(
            (1 - stick.knobSize) * stick.radius)

    def test_size_hint(self, stick):
        assert stick.sizeHint() == QtCore.QSize(120, 120)

    def test_limited_clamps_to_the_travel_circle(self, stick):
        far = QtCore.QPointF(10000., stick.height() / 2)
        clamped = stick._limited(far)
        assert clamped.x() - stick.width() / 2 == pytest.approx(stick.limit)

    def test_limited_leaves_inner_points_alone(self, stick):
        c = stick._center()
        inner = QtCore.QPointF(c.x() + 1., c.y())
        assert stick._limited(inner) == inner


class TestColors:

    def test_pad_and_knob_color_round_trip(self, stick):
        stick.setPadColor(QtGui.QColor('#102030'))
        stick.setKnobColor(QtGui.QColor('#405060'))
        assert stick.padColor == QtGui.QColor('#102030')
        assert stick.knobColor == QtGui.QColor('#405060')


class TestMouse:

    def test_a_press_outside_the_knob_does_not_drag(self, stick):
        press(stick, QtCore.QPoint(5, 5))
        assert not stick.active

    def test_a_press_on_the_knob_starts_a_drag(self, stick):
        c = stick._center()
        press(stick, c.toPoint())
        assert stick.active

    def test_dragging_to_the_right_emits_a_positive_x(self, stick, qtbot):
        c = stick._center().toPoint()
        press(stick, c)
        with qtbot.waitSignal(stick.positionChanged) as blocker:
            move(stick, c + QtCore.QPoint(int(stick.limit), 0))
        x, y = blocker.args[0]
        assert x == pytest.approx(1., abs=0.05)
        assert y == pytest.approx(0., abs=0.05)

    def test_dragging_up_emits_a_positive_y(self, stick, qtbot):
        c = stick._center().toPoint()
        press(stick, c)
        with qtbot.waitSignal(stick.positionChanged) as blocker:
            move(stick, c - QtCore.QPoint(0, int(stick.limit)))
        assert blocker.args[0][1] == pytest.approx(1., abs=0.05)

    def test_the_output_follows_the_range(self, stick, qtbot):
        stick.setRange(0., 10.)
        c = stick._center().toPoint()
        press(stick, c)
        with qtbot.waitSignal(stick.positionChanged) as blocker:
            move(stick, c + QtCore.QPoint(int(stick.limit), 0))
        assert blocker.args[0][0] == pytest.approx(10., abs=0.5)

    def test_a_small_move_inside_the_tolerance_is_silent(self, stick, qtbot):
        c = stick._center().toPoint()
        press(stick, c)
        with qtbot.assertNotEmitted(stick.positionChanged):
            move(stick, c + QtCore.QPoint(1, 0))

    def test_release_returns_the_knob_to_center(self, stick, qtbot):
        c = stick._center().toPoint()
        press(stick, c)
        move(stick, c + QtCore.QPoint(int(stick.limit), 0))
        with qtbot.waitSignal(stick.positionChanged) as blocker:
            release(stick, c)
        assert not stick.active
        assert np.allclose(blocker.args[0], 0., atol=0.05)


class TestSetKnobFraction:

    def test_does_not_emit(self, stick, qtbot):
        with qtbot.assertNotEmitted(stick.positionChanged):
            stick.setKnobFraction(0.5, 0.5)

    def test_zero_deactivates(self, stick):
        stick.setKnobFraction(0.5, 0.)
        assert stick.active
        stick.setKnobFraction(0., 0.)
        assert not stick.active

    def test_fractions_report_the_displacement(self, stick):
        stick.setKnobFraction(0.5, -0.25)
        assert np.allclose(stick._fractions(), [0.5, -0.25])


class TestPainting:

    @pytest.mark.parametrize('enabled', [True, False])
    def test_renders_enabled_and_disabled(self, stick, enabled):
        stick.setEnabled(enabled)
        stick.setKnobFraction(0.3, 0.3)
        image = stick.grab().toImage()
        assert not image.isNull()
