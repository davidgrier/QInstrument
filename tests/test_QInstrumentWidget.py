import inspect
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from qtpy import QtCore, QtWidgets
from lib.QInstrumentWidget import QInstrumentWidget
from lib.lazy import values_differ as _values_differ
from lib.QFakeInstrument import QFakeInstrument
from lib.QPollingMixin import QPollingMixin


# ---------------------------------------------------------------------------
# _uiPath
# ---------------------------------------------------------------------------

class TestUiPath:

    def test_resolves_relative_to_subclass_source(self):

        class MyWidget(QInstrumentWidget):
            UIFILE = 'MyWidget.ui'

        expected = Path(inspect.getfile(MyWidget)).parent / 'MyWidget.ui'
        assert MyWidget._uiPath() == expected

    def test_different_uifiles_give_different_paths(self):

        class WidgetA(QInstrumentWidget):
            UIFILE = 'A.ui'

        class WidgetB(QInstrumentWidget):
            UIFILE = 'B.ui'

        assert WidgetA._uiPath().name == 'A.ui'
        assert WidgetB._uiPath().name == 'B.ui'
        assert WidgetA._uiPath().parent == WidgetB._uiPath().parent


# ---------------------------------------------------------------------------
# _fakeCls — patch importlib and inspect at the module level they live in
# ---------------------------------------------------------------------------

class TestFakeCls:

    def _fake_module(self, fake_cls):
        '''Return a minimal mock that looks like a loaded fake.py.'''
        mod = MagicMock()
        mod.__all__ = [fake_cls.__name__]
        setattr(mod, fake_cls.__name__, fake_cls)
        return mod

    def _mock_module(self, package):
        m = MagicMock()
        m.__package__ = package
        return m

    def test_returns_fake_class_when_module_found(self, qtbot):
        from lib.QFakeInstrument import QFakeInstrument

        class SomeFake(QFakeInstrument):
            pass

        class W(QInstrumentWidget):
            UIFILE = 'W.ui'

        with patch('inspect.getmodule', return_value=self._mock_module('mypkg')), \
             patch('importlib.import_module',
                   return_value=self._fake_module(SomeFake)) as mock_import:
            result = W._fakeCls()

        mock_import.assert_called_once_with('.fake', package='mypkg')
        assert result is SomeFake

    def test_returns_none_when_import_error(self, qtbot):

        class W(QInstrumentWidget):
            UIFILE = 'W.ui'

        with patch('inspect.getmodule', return_value=self._mock_module('mypkg')), \
             patch('importlib.import_module', side_effect=ImportError):
            assert W._fakeCls() is None

    def test_returns_none_when_no_package_and_no_syspath_match(self, qtbot):

        class W(QInstrumentWidget):
            UIFILE = 'W.ui'

        with patch('inspect.getmodule', return_value=self._mock_module('')), \
             patch('inspect.getfile', return_value='/no/match/widget.py'), \
             patch.object(sys, 'path', []):
            assert W._fakeCls() is None

    def test_syspath_fallback_derives_package_from_file_path(
            self, qtbot, tmp_path):
        from lib.QFakeInstrument import QFakeInstrument

        class SomeFake(QFakeInstrument):
            pass

        widget_dir = tmp_path / 'MyPkg' / 'instruments' / 'Dev'
        widget_dir.mkdir(parents=True)

        class W(QInstrumentWidget):
            UIFILE = 'W.ui'

        with patch('inspect.getmodule', return_value=self._mock_module('')), \
             patch('inspect.getfile',
                   return_value=str(widget_dir / 'widget.py')), \
             patch('importlib.import_module',
                   return_value=self._fake_module(SomeFake)) as mock_import, \
             patch.object(sys, 'path', [str(tmp_path)]):
            result = W._fakeCls()

        mock_import.assert_called_once_with(
            '.fake', package='MyPkg.instruments.Dev')
        assert result is SomeFake


# ---------------------------------------------------------------------------
# Helpers for widget-binding tests
# ---------------------------------------------------------------------------

class TwoPropertyDevice(QFakeInstrument):
    '''Fake device with float "frequency" and int "count" properties.'''
    def _registerProperties(self):
        self._frequency = 0.0
        self._count = 0
        self.registerProperty(
            'frequency',
            getter=lambda: self._frequency,
            setter=lambda v: setattr(self, '_frequency', float(v)),
            ptype=float)
        self.registerProperty(
            'count',
            getter=lambda: self._count,
            setter=lambda v: setattr(self, '_count', int(v)),
            ptype=int)


class ClosedDevice(TwoPropertyDevice):
    def isOpen(self) -> bool:
        return False


def _make_widget(qtbot, device):
    '''Build a QInstrumentWidget with mocked uic containing three widgets:
    ``frequency`` (QDoubleSpinBox), ``count`` (QSpinBox), ``extra`` (QSpinBox).
    Only ``frequency`` and ``count`` have matching device properties.
    '''
    freq_w = QtWidgets.QDoubleSpinBox()
    freq_w.setRange(-1e9, 1e9)
    count_w = QtWidgets.QSpinBox()
    count_w.setRange(-1000000, 1000000)
    extra_w = QtWidgets.QSpinBox()

    def fake_loadUi(path, parent):
        for name, widget in [('frequency', freq_w),
                              ('count', count_w),
                              ('extra', extra_w)]:
            widget.setObjectName(name)
            setattr(parent, name, widget)

    class TestW(QInstrumentWidget):
        UIFILE = 'TestW.ui'

    with patch('qtpy.uic.loadUi', side_effect=fake_loadUi):
        w = TestW(device=device)
    qtbot.addWidget(w)
    return w


# ---------------------------------------------------------------------------
# _identifyProperties
# ---------------------------------------------------------------------------

class TestIdentifyProperties:

    def test_matched_widget_names_in_properties(self, qtbot):
        w = _make_widget(qtbot, TwoPropertyDevice())
        assert set(w.properties) == {'frequency', 'count'}

    def test_unmatched_widget_excluded_from_properties(self, qtbot):
        w = _make_widget(qtbot, TwoPropertyDevice())
        assert 'extra' not in w.properties

    def test_device_property_without_widget_excluded(self, qtbot):
        freq_w = QtWidgets.QDoubleSpinBox()

        def fake_loadUi(path, parent):
            freq_w.setObjectName('frequency')
            parent.frequency = freq_w

        class TinyW(QInstrumentWidget):
            UIFILE = 'TinyW.ui'

        with patch('qtpy.uic.loadUi', side_effect=fake_loadUi):
            w = TinyW(device=TwoPropertyDevice())
        qtbot.addWidget(w)
        assert 'count' not in w.properties
        assert 'frequency' in w.properties


# ---------------------------------------------------------------------------
# _syncProperties
# ---------------------------------------------------------------------------

class TestSyncProperties:

    def test_float_widget_initialized_from_device(self, qtbot):
        device = TwoPropertyDevice()
        device._frequency = 880.0
        w = _make_widget(qtbot, device)
        assert w.frequency.value() == pytest.approx(880.0)

    def test_int_widget_initialized_from_device(self, qtbot):
        device = TwoPropertyDevice()
        device._count = 7
        w = _make_widget(qtbot, device)
        assert w.count.value() == 7

    def test_widget_not_synced_when_device_closed(self, qtbot):
        device = ClosedDevice()
        device._frequency = 999.0
        w = _make_widget(qtbot, device)
        assert w.frequency.value() == pytest.approx(0.0)

    def test_widget_disabled_when_device_closed(self, qtbot):
        w = _make_widget(qtbot, ClosedDevice())
        assert not w.isEnabled()


# ---------------------------------------------------------------------------
# _connectSignals / _setDeviceProperty
# ---------------------------------------------------------------------------

class TestConnectSignals:

    def test_float_widget_change_updates_device(self, qtbot):
        device = TwoPropertyDevice()
        w = _make_widget(qtbot, device)
        w.frequency.setValue(1000.0)
        assert device._frequency == pytest.approx(1000.0)

    def test_int_widget_change_updates_device(self, qtbot):
        device = TwoPropertyDevice()
        w = _make_widget(qtbot, device)
        w.count.setValue(5)
        assert device._count == 5

    def test_propertyChanged_emitted_on_widget_change(self, qtbot):
        device = TwoPropertyDevice()
        w = _make_widget(qtbot, device)
        with qtbot.waitSignal(w.propertyChanged, timeout=500) as blocker:
            w.frequency.setValue(500.0)
        assert blocker.args[0] == 'frequency'

    def test_unmatched_widget_change_does_not_emit_propertyChanged(self, qtbot):
        device = TwoPropertyDevice()
        w = _make_widget(qtbot, device)
        with qtbot.assertNotEmitted(w.propertyChanged):
            w.extra.setValue(42)


# ---------------------------------------------------------------------------
# Debounce
# ---------------------------------------------------------------------------

class DebouncedDevice(QFakeInstrument):
    '''Fake device with a ``power`` property that declares debounce=100.'''
    def _registerProperties(self):
        self._power = 0.0
        self.registerProperty(
            'power',
            getter=lambda: self._power,
            setter=lambda v: setattr(self, '_power', float(v)),
            ptype=float,
            debounce=100)


def _make_debounced_widget(qtbot, device):
    power_w = QtWidgets.QDoubleSpinBox()
    power_w.setRange(0., 1000.)

    def fake_loadUi(path, parent):
        power_w.setObjectName('power')
        parent.power = power_w

    class DebouncedW(QInstrumentWidget):
        UIFILE = 'DebouncedW.ui'

    with patch('qtpy.uic.loadUi', side_effect=fake_loadUi):
        w = DebouncedW(device=device)
    qtbot.addWidget(w)
    return w


class TestDebounce:

    def test_device_not_updated_immediately(self, qtbot):
        device = DebouncedDevice()
        w = _make_debounced_widget(qtbot, device)
        w.power.setValue(50.0)
        # device must not be updated synchronously
        assert device._power == pytest.approx(0.0)

    def test_device_updated_after_debounce_interval(self, qtbot):
        device = DebouncedDevice()
        w = _make_debounced_widget(qtbot, device)
        with qtbot.waitSignal(w.propertyChanged, timeout=500):
            w.power.setValue(75.0)
        assert device._power == pytest.approx(75.0)

    def test_rapid_changes_send_only_last_value(self, qtbot):
        device = DebouncedDevice()
        w = _make_debounced_widget(qtbot, device)
        # Emit several rapid changes; only the last should reach the device.
        for v in (10.0, 20.0, 30.0, 40.0):
            w.power.setValue(v)
        with qtbot.waitSignal(w.propertyChanged, timeout=500) as blocker:
            pass
        assert blocker.args == ['power', 40.0]
        assert device._power == pytest.approx(40.0)

    def test_propertyChanged_carries_debounced_value(self, qtbot):
        device = DebouncedDevice()
        w = _make_debounced_widget(qtbot, device)
        with qtbot.waitSignal(w.propertyChanged, timeout=500) as blocker:
            w.power.setValue(99.0)
        assert blocker.args[0] == 'power'
        assert blocker.args[1] == pytest.approx(99.0)


# ---------------------------------------------------------------------------
# _values_differ
# ---------------------------------------------------------------------------

class TestValuesDiffer:

    def test_equal_ints(self):
        assert _values_differ(1, 1) is False

    def test_unequal_ints(self):
        assert _values_differ(1, 2) is True

    def test_equal_strings(self):
        assert _values_differ('a', 'a') is False

    def test_unequal_strings(self):
        assert _values_differ('a', 'b') is True

    def test_equal_bools(self):
        assert _values_differ(True, True) is False

    def test_unequal_bools(self):
        assert _values_differ(True, False) is True

    def test_equal_floats(self):
        assert _values_differ(1.0, 1.0) is False

    def test_nearly_equal_floats_within_tolerance(self):
        assert _values_differ(1.0, 1.0 + 1e-10) is False

    def test_floats_outside_tolerance(self):
        assert _values_differ(1.0, 2.0) is True


# ---------------------------------------------------------------------------
# _restoreSettings
# ---------------------------------------------------------------------------

class TestRestoreSettings:
    '''Tests for QInstrumentWidget._restoreSettings().

    The Configure object and QReconcileDialog are patched so no file I/O
    or Qt dialogs are needed.
    '''

    def _make_restore_widget(self, qtbot, device, tmp_path):
        '''Build a minimal widget with a real Configure pointing at tmp_path.'''
        freq_w = QtWidgets.QDoubleSpinBox()
        freq_w.setRange(-1e9, 1e9)

        def fake_loadUi(path, parent):
            freq_w.setObjectName('frequency')
            setattr(parent, 'frequency', freq_w)

        class RestoreW(QInstrumentWidget):
            UIFILE = 'RestoreW.ui'

        with patch('qtpy.uic.loadUi', side_effect=fake_loadUi):
            w = RestoreW(device=device)

        from lib.Configure import Configure
        w._configure = Configure(
            datadir=str(tmp_path / 'data'),
            configdir=str(tmp_path / 'config'))
        qtbot.addWidget(w)
        return w

    def test_no_config_file_saves_hardware_values(self, qtbot, tmp_path):
        device = TwoPropertyDevice()
        device._frequency = 123.0
        w = self._make_restore_widget(qtbot, device, tmp_path)
        w._restoreSettings()
        saved = w._configure.read(device)
        assert saved is not None
        assert saved['frequency'] == pytest.approx(123.0)

    def test_no_config_file_does_not_change_hardware(self, qtbot, tmp_path):
        device = TwoPropertyDevice()
        device._frequency = 42.0
        w = self._make_restore_widget(qtbot, device, tmp_path)
        w._restoreSettings()
        assert device._frequency == pytest.approx(42.0)

    def test_matching_config_no_dialog_shown(self, qtbot, tmp_path):
        device = TwoPropertyDevice()
        device._frequency = 10.0
        device._count = 3
        w = self._make_restore_widget(qtbot, device, tmp_path)
        w._configure.save(device)

        with patch('lib.QInstrumentWidget.QReconcileDialog') as MockDialog:
            w._restoreSettings()
        MockDialog.assert_not_called()

    def test_mismatch_shows_dialog(self, qtbot, tmp_path):
        device = TwoPropertyDevice()
        device._frequency = 10.0
        w = self._make_restore_widget(qtbot, device, tmp_path)
        w._configure.save(device)

        device._frequency = 99.0

        mock_dialog = MagicMock()
        mock_dialog.exec.return_value = True
        mock_dialog.keep_hardware = True
        with patch('lib.QInstrumentWidget.QReconcileDialog',
                   return_value=mock_dialog) as MockCls:
            w._restoreSettings()
        MockCls.assert_called_once()

    def test_keep_hardware_updates_config_file(self, qtbot, tmp_path):
        device = TwoPropertyDevice()
        device._frequency = 10.0
        w = self._make_restore_widget(qtbot, device, tmp_path)
        w._configure.save(device)

        device._frequency = 99.0

        mock_dialog = MagicMock()
        mock_dialog.exec.return_value = True
        mock_dialog.keep_hardware = True
        with patch('lib.QInstrumentWidget.QReconcileDialog',
                   return_value=mock_dialog):
            w._restoreSettings()

        saved = w._configure.read(device)
        assert saved['frequency'] == pytest.approx(99.0)
        assert device._frequency == pytest.approx(99.0)

    def test_use_saved_pushes_to_hardware(self, qtbot, tmp_path):
        device = TwoPropertyDevice()
        device._frequency = 10.0
        w = self._make_restore_widget(qtbot, device, tmp_path)
        w._configure.save(device)

        device._frequency = 99.0

        mock_dialog = MagicMock()
        mock_dialog.exec.return_value = True
        mock_dialog.keep_hardware = False
        with patch('lib.QInstrumentWidget.QReconcileDialog',
                   return_value=mock_dialog):
            w._restoreSettings()

        assert device._frequency == pytest.approx(10.0)

    def test_dismissed_dialog_keeps_hardware(self, qtbot, tmp_path):
        device = TwoPropertyDevice()
        device._frequency = 10.0
        w = self._make_restore_widget(qtbot, device, tmp_path)
        w._configure.save(device)

        device._frequency = 55.0

        mock_dialog = MagicMock()
        mock_dialog.exec.return_value = False  # dismissed
        mock_dialog.keep_hardware = True
        with patch('lib.QInstrumentWidget.QReconcileDialog',
                   return_value=mock_dialog):
            w._restoreSettings()

        assert device._frequency == pytest.approx(55.0)

    def test_hardware_dominant_passed_to_dialog(self, qtbot, tmp_path):
        device = TwoPropertyDevice()
        device._frequency = 10.0
        w = self._make_restore_widget(qtbot, device, tmp_path)
        w._configure.save(device)
        device._frequency = 99.0

        class HWDominantW(QInstrumentWidget):
            UIFILE = 'HWDominantW.ui'
            HARDWARE_DOMINANT = True

        w.HARDWARE_DOMINANT = True

        mock_dialog = MagicMock()
        mock_dialog.exec.return_value = True
        mock_dialog.keep_hardware = True
        with patch('lib.QInstrumentWidget.QReconcileDialog',
                   return_value=mock_dialog) as MockCls:
            w._restoreSettings()

        _, kwargs = MockCls.call_args
        assert kwargs.get('hardware_dominant') is True


# ---------------------------------------------------------------------------
# Polling integration — startPolling / stopPolling
# ---------------------------------------------------------------------------

class PollingDevice(QPollingMixin, QFakeInstrument):
    '''Fake device that also has startPolling/stopPolling slots.'''


class TestPollingIntegration:

    def _make_polling_widget(self, qtbot):
        device = PollingDevice()

        def fake_loadUi(path, parent):
            pass

        class PollingW(QInstrumentWidget):
            UIFILE = 'PollingW.ui'

        with patch('qtpy.uic.loadUi', side_effect=fake_loadUi):
            w = PollingW(device=device)
        qtbot.addWidget(w)
        return w, device

    def test_firstShow_does_not_auto_start_polling(self, qtbot):
        w, device = self._make_polling_widget(qtbot)
        with patch.object(w, '_restoreSettings'), \
             patch.object(w, '_syncProperties'), \
             patch('lib.QInstrumentWidget.QtCore.QMetaObject.invokeMethod'
                   ) as mock_invoke:
            w._firstShow()
        mock_invoke.assert_not_called()

    def test_closeEvent_calls_stopPolling_when_thread_running(self, qtbot):
        w, device = self._make_polling_widget(qtbot)
        w._thread = MagicMock()
        with patch.object(device, 'stopPolling') as mock_stop:
            w.close()
        mock_stop.assert_called_once()

    def test_closeEvent_does_not_call_stopPolling_when_no_thread(
            self, qtbot):
        w, device = self._make_polling_widget(qtbot)
        assert w._thread is None
        with patch.object(device, 'stopPolling') as mock_stop:
            w.close()
        mock_stop.assert_not_called()
