from unittest.mock import MagicMock, patch

import pytest
from qtpy import QtCore, QtWidgets

from QInstrumentRack import QInstrumentRack, _InstrumentSlot
from lib.QInstrumentWidget import QInstrumentWidget


# ---------------------------------------------------------------------------
# Minimal fake widget — no device, no UI file needed
# ---------------------------------------------------------------------------

class _FakeWidget(QtWidgets.QWidget):
    '''Stand-in for QInstrumentWidget in rack tests.'''
    settings = {}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def rack(qtbot):
    w = QInstrumentRack()
    qtbot.addWidget(w)
    return w


@pytest.fixture
def rack_with_two(qtbot):
    w = QInstrumentRack()
    qtbot.addWidget(w)
    w.addInstrument(_FakeWidget(), 'Alpha')
    w.addInstrument(_FakeWidget(), 'Beta')
    return w


# ---------------------------------------------------------------------------
# addInstrument / addInstruments
# ---------------------------------------------------------------------------

class TestAddInstrument:

    def test_slot_count_increases(self, rack):
        assert rack._slots.count() == 0
        rack.addInstrument(_FakeWidget(), 'A')
        assert rack._slots.count() == 1

    def test_name_derived_from_class_when_omitted(self, rack):
        rack.addInstrument(_FakeWidget())
        slot = rack._slotAt(0)
        assert slot._name == '_Fake'

    def test_explicit_name_is_used(self, rack):
        rack.addInstrument(_FakeWidget(), 'MyInst')
        assert rack._slotAt(0)._name == 'MyInst'

    def test_add_multiple(self, rack):
        rack.addInstruments([_FakeWidget(), _FakeWidget()])
        assert rack._slots.count() == 2


# ---------------------------------------------------------------------------
# clearInstruments / _removeInstrument
# ---------------------------------------------------------------------------

class TestRemoveInstrument:

    def test_clear_empties_rack(self, rack_with_two):
        rack_with_two.clearInstruments()
        assert rack_with_two._slots.count() == 0

    def test_remove_by_name(self, rack_with_two):
        rack_with_two._removeInstrument('Alpha')
        assert rack_with_two._slots.count() == 1
        assert rack_with_two._slotAt(0)._name == 'Beta'

    def test_remove_unknown_name_is_noop(self, rack_with_two):
        rack_with_two._removeInstrument('NoSuchInstrument')
        assert rack_with_two._slots.count() == 2


# ---------------------------------------------------------------------------
# settings property
# ---------------------------------------------------------------------------

class TestSettings:

    def test_settings_returns_names_in_order(self, rack_with_two):
        assert rack_with_two.settings == {'instruments': ['Alpha', 'Beta']}

    def test_settings_setter_reloads(self, rack_with_two):
        with patch.object(rack_with_two, 'addInstrumentsByNames') as mock_add:
            rack_with_two.settings = {'instruments': ['X', 'Y']}
        mock_add.assert_called_once_with(['X', 'Y'])

    def test_settings_empty_when_rack_clear(self, rack):
        assert rack.settings == {'instruments': []}


# ---------------------------------------------------------------------------
# editable property
# ---------------------------------------------------------------------------

class TestEditable:

    def test_default_is_true(self, rack):
        assert rack.editable is True

    def test_toolbar_hidden_when_not_editable(self, rack):
        rack.editable = False
        assert not rack._toolbar.isVisible()

    def test_toolbar_visible_when_editable(self, rack):
        rack.editable = False
        rack.editable = True
        assert not rack._toolbar.isHidden()

    def test_slot_handles_hidden_when_not_editable(self, rack_with_two):
        rack_with_two.editable = False
        slot = rack_with_two._slotAt(0)
        assert slot._handle.isHidden()
        assert slot._closeButton.isHidden()

    def test_slot_handles_shown_when_editable(self, rack_with_two):
        rack_with_two.editable = False
        rack_with_two.editable = True
        slot = rack_with_two._slotAt(0)
        assert not slot._handle.isHidden()
        assert not slot._closeButton.isHidden()


# ---------------------------------------------------------------------------
# _moveSlot
# ---------------------------------------------------------------------------

class TestMoveSlot:

    def test_move_first_to_second(self, rack_with_two):
        slot_alpha = rack_with_two._slotAt(0)
        # Use the geometry of Beta as the drop target
        target = rack_with_two._slotAt(1)
        drop_pos = rack_with_two.mapToGlobal(target.geometry().center())
        rack_with_two._moveSlot(slot_alpha, drop_pos)
        assert rack_with_two._slotAt(0)._name == 'Beta'
        assert rack_with_two._slotAt(1)._name == 'Alpha'

    def test_drop_on_self_is_noop(self, rack_with_two):
        slot_alpha = rack_with_two._slotAt(0)
        drop_pos = rack_with_two.mapToGlobal(slot_alpha.geometry().center())
        rack_with_two._moveSlot(slot_alpha, drop_pos)
        assert rack_with_two._slotAt(0)._name == 'Alpha'


# ---------------------------------------------------------------------------
# _hoverSlot / setHighlighted
# ---------------------------------------------------------------------------

class TestHover:

    def test_target_slot_highlighted(self, rack_with_two):
        slot_alpha = rack_with_two._slotAt(0)
        slot_beta = rack_with_two._slotAt(1)
        # Show widgets so geometries are non-zero
        rack_with_two.show()
        hover_pos = rack_with_two.mapToGlobal(slot_beta.geometry().center())
        rack_with_two._hoverSlot(slot_alpha, hover_pos)
        assert slot_beta._dropIndicator.isVisible()
        assert not slot_alpha._dropIndicator.isVisible()

    def test_move_clears_all_highlights(self, rack_with_two):
        rack_with_two.show()
        slot_alpha = rack_with_two._slotAt(0)
        slot_beta = rack_with_two._slotAt(1)
        slot_beta.setHighlighted(True)
        drop_pos = rack_with_two.mapToGlobal(slot_beta.geometry().center())
        rack_with_two._moveSlot(slot_alpha, drop_pos)
        assert not slot_beta._dropIndicator.isVisible()


# ---------------------------------------------------------------------------
# availableInstruments / _findInstrumentModule
# ---------------------------------------------------------------------------

class TestAvailableInstruments:

    def test_returns_sorted_list(self):
        names = QInstrumentRack.availableInstruments()
        assert names == sorted(names)

    def test_ds345_present(self):
        assert 'DS345' in QInstrumentRack.availableInstruments()

    def test_find_module_returns_none_for_unknown(self):
        assert QInstrumentRack._findInstrumentModule('NoSuchThing') is None

    def test_find_module_returns_dotted_path_for_known(self):
        path = QInstrumentRack._findInstrumentModule('DS345')
        assert path is not None
        assert path.endswith('.widget')
        assert 'DS345' in path


# ---------------------------------------------------------------------------
# showEvent / closeEvent (save/restore gating)
# ---------------------------------------------------------------------------

class TestPersistence:

    def test_restore_called_on_first_show_when_empty(self, rack, qtbot):
        with patch.object(rack._configure, 'restore') as mock_restore:
            qtbot.addWidget(rack)
            rack.show()
        mock_restore.assert_called_once_with(rack)

    def test_restore_not_called_when_instruments_preloaded(self, qtbot):
        w = QInstrumentRack()
        w.addInstrument(_FakeWidget(), 'X')
        qtbot.addWidget(w)
        with patch.object(w._configure, 'restore') as mock_restore:
            w.show()
        mock_restore.assert_not_called()

    def test_save_called_on_close_after_show(self, rack, qtbot):
        rack.show()
        with patch.object(rack._configure, 'save') as mock_save:
            rack.close()
        mock_save.assert_called_once_with(rack)

    def test_save_not_called_on_close_without_show(self, rack):
        with patch.object(rack._configure, 'save') as mock_save:
            rack.close()
        mock_save.assert_not_called()
