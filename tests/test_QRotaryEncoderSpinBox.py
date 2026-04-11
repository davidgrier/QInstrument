import pytest
from qtpy import QtCore
from widgets.QRotaryEncoderSpinBox import QRotaryEncoderSpinBox


@pytest.fixture
def spinbox(qtbot):
    w = QRotaryEncoderSpinBox()
    qtbot.addWidget(w)
    return w


# ---------------------------------------------------------------------------
# Delegation to QDoubleSpinBox
# ---------------------------------------------------------------------------

class TestDelegation:

    def test_set_and_get_value(self, spinbox):
        spinbox.setRange(0., 10.)
        spinbox.setValue(5.)
        assert spinbox.value() == pytest.approx(5.)

    def test_set_minimum(self, spinbox):
        spinbox.setMinimum(1.)
        assert spinbox.minimum() == pytest.approx(1.)

    def test_set_maximum(self, spinbox):
        spinbox.setMaximum(99.)
        assert spinbox.maximum() == pytest.approx(99.)

    def test_set_range(self, spinbox):
        spinbox.setRange(2., 8.)
        assert spinbox.minimum() == pytest.approx(2.)
        assert spinbox.maximum() == pytest.approx(8.)

    def test_set_single_step(self, spinbox):
        spinbox.setSingleStep(0.5)
        assert spinbox.singleStep() == pytest.approx(0.5)

    def test_set_decimals(self, spinbox):
        spinbox.setDecimals(3)
        assert spinbox.decimals() == 3

    def test_value_changed_signal_fires(self, spinbox, qtbot):
        spinbox.setRange(0., 10.)
        spinbox.setValue(0.)
        with qtbot.waitSignal(spinbox.valueChanged):
            spinbox.setValue(3.)


# ---------------------------------------------------------------------------
# title
# ---------------------------------------------------------------------------

class TestTitle:

    def test_set_and_get_title(self, spinbox):
        spinbox.setTitle('Power [W]')
        assert spinbox.title() == 'Power [W]'

    def test_empty_title(self, spinbox):
        spinbox.setTitle('')
        assert spinbox.title() == ''


# ---------------------------------------------------------------------------
# setColors / color interpolation
# ---------------------------------------------------------------------------

class TestColors:

    def test_default_colors_set(self, spinbox):
        assert spinbox.colors() == ('white', 'red')

    def test_set_custom_colors(self, spinbox):
        spinbox.setColors(('white', '#68ff00'))
        assert spinbox.colors() == ('white', '#68ff00')

    def test_set_colors_none_disables(self, spinbox):
        spinbox.setColors(None)
        assert spinbox.colors() is None

    def test_style_sheet_updated_signal_fires(self, spinbox, qtbot):
        spinbox.setRange(0., 10.)
        spinbox.setColors(('white', 'red'))
        with qtbot.waitSignal(spinbox.styleSheetUpdated):
            spinbox.setValue(5.)

    def test_set_colors_multiple_times_no_double_connect(self, spinbox, qtbot):
        spinbox.setRange(0., 10.)
        spinbox.setColors(('white', 'blue'))
        spinbox.setColors(('white', 'green'))
        signals = []
        spinbox.styleSheetUpdated.connect(signals.append)
        spinbox.setValue(3.)
        assert len(signals) == 1


# ---------------------------------------------------------------------------
# Arrow key suppression
# ---------------------------------------------------------------------------

class TestArrowKeySuppression:

    def test_up_arrow_blocked(self, spinbox, qtbot):
        spinbox.setRange(0., 10.)
        spinbox.setValue(5.)
        from qtpy.QtCore import Qt
        from qtpy.QtGui import QKeyEvent
        from qtpy.QtCore import QEvent
        event = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Up, Qt.KeyboardModifier.NoModifier)
        assert spinbox._filter.eventFilter(spinbox._spinbox, event) is True

    def test_down_arrow_blocked(self, spinbox, qtbot):
        from qtpy.QtCore import Qt
        from qtpy.QtGui import QKeyEvent
        from qtpy.QtCore import QEvent
        event = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Down, Qt.KeyboardModifier.NoModifier)
        assert spinbox._filter.eventFilter(spinbox._spinbox, event) is True

    def test_other_keys_not_blocked(self, spinbox, qtbot):
        from qtpy.QtCore import Qt
        from qtpy.QtGui import QKeyEvent
        from qtpy.QtCore import QEvent
        event = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Return, Qt.KeyboardModifier.NoModifier)
        assert spinbox._filter.eventFilter(spinbox._spinbox, event) is False
