import pytest
from lib.QReconcileDialog import QReconcileDialog


HW    = {'frequency': 100.0, 'count': 3}
SAVED = {'frequency': 200.0, 'count': 3}
DIFF  = ['frequency']


@pytest.fixture
def dialog(qtbot):
    d = QReconcileDialog(HW, SAVED, DIFF)
    qtbot.addWidget(d)
    return d


# ---------------------------------------------------------------------------
# Default state
# ---------------------------------------------------------------------------

class TestDefault:

    def test_keep_hardware_by_default(self, dialog):
        assert dialog.keep_hardware is True

    def test_saved_btn_is_default_when_not_hardware_dominant(self, qtbot):
        d = QReconcileDialog(HW, SAVED, DIFF, hardware_dominant=False)
        qtbot.addWidget(d)
        assert d.keep_hardware is True      # no button pressed yet

    def test_hardware_btn_is_default_when_hardware_dominant(self, qtbot):
        d = QReconcileDialog(HW, SAVED, DIFF, hardware_dominant=True)
        qtbot.addWidget(d)
        assert d.keep_hardware is True


# ---------------------------------------------------------------------------
# Button actions
# ---------------------------------------------------------------------------

class TestButtons:

    def test_keep_hardware_button_sets_keep_hardware_true(self, qtbot, dialog):
        dialog._keep_hardware()
        assert dialog.keep_hardware is True

    def test_use_saved_button_sets_keep_hardware_false(self, qtbot, dialog):
        dialog._use_saved()
        assert dialog.keep_hardware is False

    def test_keep_hardware_button_accepts_dialog(self, qtbot, dialog):
        dialog._keep_hardware()
        assert dialog.result() == dialog.DialogCode.Accepted

    def test_use_saved_button_accepts_dialog(self, qtbot, dialog):
        dialog._use_saved()
        assert dialog.result() == dialog.DialogCode.Accepted


# ---------------------------------------------------------------------------
# Table content
# ---------------------------------------------------------------------------

class TestTableContent:

    def test_table_has_one_row_per_diff_key(self, dialog):
        table = dialog.findChild(
            __import__('qtpy.QtWidgets', fromlist=['QTableWidget'])
            .QTableWidget)
        assert table.rowCount() == len(DIFF)

    def test_table_shows_hardware_value(self, dialog):
        from qtpy.QtWidgets import QTableWidget
        table = dialog.findChild(QTableWidget)
        assert table.item(0, 1).text() == str(HW['frequency'])

    def test_table_shows_saved_value(self, dialog):
        from qtpy.QtWidgets import QTableWidget
        table = dialog.findChild(QTableWidget)
        assert table.item(0, 2).text() == str(SAVED['frequency'])

    def test_table_shows_property_name(self, dialog):
        from qtpy.QtWidgets import QTableWidget
        table = dialog.findChild(QTableWidget)
        assert table.item(0, 0).text() == 'frequency'
