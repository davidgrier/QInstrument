import logging
import pytest
from unittest.mock import MagicMock, patch

from lib.QFakeInstrument import QFakeInstrument
from lib.QInstrumentTree import QInstrumentTree


# ---------------------------------------------------------------------------
# Helpers — minimal device and tree subclasses
# ---------------------------------------------------------------------------

class TreeDevice(QFakeInstrument):
    '''Fake device with float, int, str, and read-only properties + a method.'''

    def _registerProperties(self):
        self._frequency = 0.0
        self._count = 0
        self.registerProperty(
            'frequency',
            getter=lambda: self._frequency,
            setter=lambda v: setattr(self, '_frequency', float(v)),
            ptype=float, minimum=0., maximum=1000., step=0.1)
        self.registerProperty(
            'count',
            getter=lambda: self._count,
            setter=lambda v: setattr(self, '_count', int(v)),
            ptype=int)
        self.registerProperty(
            'label',
            getter=lambda: 'FIXED',
            setter=None,
            ptype=str)

    def _registerMethods(self):
        self._reset_calls = 0
        self.registerMethod('reset', lambda: setattr(
            self, '_reset_calls', self._reset_calls + 1))


@pytest.fixture
def device(qtbot):
    return TreeDevice()


@pytest.fixture
def tree(qtbot, device):
    t = QInstrumentTree(device=device)
    qtbot.addWidget(t)
    return t


# ---------------------------------------------------------------------------
# _resolveFields
# ---------------------------------------------------------------------------

class TestResolveFields:

    def test_no_fields_shows_all_props_and_methods(self, tree, device):
        assert set(tree._visibleProps) == {'frequency', 'count', 'label'}
        assert tree._visibleMethods == ['reset']

    def test_fields_restricts_to_named_props(self, qtbot, device):
        t = QInstrumentTree(device=device, fields=['frequency'])
        qtbot.addWidget(t)
        assert t._visibleProps == ['frequency']
        assert t._visibleMethods == []

    def test_fields_preserves_order(self, qtbot, device):
        t = QInstrumentTree(device=device, fields=['count', 'frequency'])
        qtbot.addWidget(t)
        assert t._visibleProps == ['count', 'frequency']

    def test_unknown_field_falls_back_to_all(self, qtbot, device, caplog):
        with caplog.at_level(logging.WARNING):
            t = QInstrumentTree(device=device, fields=['nosuchprop'])
        qtbot.addWidget(t)
        assert set(t._visibleProps) == {'frequency', 'count', 'label'}
        assert 'nosuchprop' in caplog.text

    def test_method_name_in_fields_goes_to_visible_methods(self, qtbot, device):
        t = QInstrumentTree(device=device, fields=['frequency', 'reset'])
        qtbot.addWidget(t)
        assert 'frequency' in t._visibleProps
        assert 'reset' in t._visibleMethods


# ---------------------------------------------------------------------------
# _buildTree — parameter types and metadata
# ---------------------------------------------------------------------------

class TestBuildTree:

    def test_float_prop_gets_float_parameter(self, tree):
        assert tree._params['frequency'].type() == 'float'

    def test_int_prop_gets_int_parameter(self, tree):
        assert tree._params['count'].type() == 'int'

    def test_str_prop_gets_str_parameter(self, tree):
        assert tree._params['label'].type() == 'str'

    def test_method_gets_action_parameter(self, tree):
        assert tree._params['reset'].type() == 'action'

    def test_readonly_prop_is_not_editable(self, tree):
        assert tree._params['label'].opts.get('readonly') is True

    def test_writable_prop_is_editable(self, tree):
        assert not tree._params['frequency'].opts.get('readonly', False)

    def test_limits_applied_from_metadata(self, tree):
        limits = tree._params['frequency'].opts.get('limits')
        assert limits == (0., 1000.)

    def test_step_applied_from_metadata(self, tree):
        assert tree._params['frequency'].opts.get('step') == pytest.approx(0.1)

    def test_all_visible_props_have_params(self, tree):
        for name in tree._visibleProps:
            assert name in tree._params

    def test_all_visible_methods_have_params(self, tree):
        for name in tree._visibleMethods:
            assert name in tree._params


# ---------------------------------------------------------------------------
# _syncProperties
# ---------------------------------------------------------------------------

class TestSyncProperties:

    def test_sync_calls_device_get_for_each_prop(self, tree, device):
        calls = []
        original_get = device.get
        device.get = lambda k: calls.append(k) or original_get(k)
        tree._syncProperties()
        for name in tree._visibleProps:
            assert name in calls

    def test_param_updated_with_device_value(self, qtbot, device):
        device._frequency = 750.0
        t = QInstrumentTree(device=device)
        qtbot.addWidget(t)
        assert t._params['frequency'].value() == pytest.approx(750.0)


# ---------------------------------------------------------------------------
# _onParamChanged → device.set
# ---------------------------------------------------------------------------

class TestOnParamChanged:

    def test_param_change_calls_device_set(self, tree, device):
        tree._onParamChanged('frequency', 500.0)
        assert device._frequency == pytest.approx(500.0)

    def test_param_change_blocked_while_updating(self, tree, device):
        device._frequency = 1.0
        tree._updating = True
        tree._onParamChanged('frequency', 999.0)
        assert device._frequency == pytest.approx(1.0)

    def test_updating_flag_cleared_after_change(self, tree):
        tree._onParamChanged('frequency', 1.0)
        assert tree._updating is False


# ---------------------------------------------------------------------------
# _onDevicePropertyValue → parameter update
# ---------------------------------------------------------------------------

class TestOnDevicePropertyValue:

    def test_device_value_updates_param(self, tree):
        tree._onDevicePropertyValue('frequency', 300.0)
        assert tree._params['frequency'].value() == pytest.approx(300.0)

    def test_unknown_property_ignored(self, tree):
        tree._onDevicePropertyValue('nosuchprop', 1.0)  # must not raise

    def test_update_blocked_while_updating(self, tree):
        tree._params['frequency'].setValue(0.0)
        tree._updating = True
        tree._onDevicePropertyValue('frequency', 999.0)
        assert tree._params['frequency'].value() == pytest.approx(0.0)

    def test_updating_flag_cleared_after_update(self, tree):
        tree._onDevicePropertyValue('frequency', 1.0)
        assert tree._updating is False


# ---------------------------------------------------------------------------
# _connectSignals — method button triggers device.execute
# ---------------------------------------------------------------------------

class TestConnectSignalsMethod:

    def test_action_param_activation_calls_execute(self, tree, device):
        tree._params['reset'].activate()
        assert device._reset_calls == 1


# ---------------------------------------------------------------------------
# propertyValue signal round-trip
# ---------------------------------------------------------------------------

class TestPropertyValueRoundTrip:

    def test_device_set_updates_tree_param(self, qtbot, tree, device):
        device.set('frequency', 123.0)
        qtbot.wait(50)
        assert tree._params['frequency'].value() == pytest.approx(123.0)


# ---------------------------------------------------------------------------
# _restoreSettings
# ---------------------------------------------------------------------------

class TestRestoreSettings:

    def _make_tree(self, qtbot, device, tmp_path):
        from lib.Configure import Configure
        t = QInstrumentTree(device=device)
        t._configure = Configure(
            datadir=str(tmp_path / 'data'),
            configdir=str(tmp_path / 'config'))
        qtbot.addWidget(t)
        return t

    def test_no_config_file_saves_hardware_values(self, qtbot, device, tmp_path):
        device._frequency = 200.0
        t = self._make_tree(qtbot, device, tmp_path)
        t._restoreSettings()
        saved = t._configure.read(device)
        assert saved is not None
        assert saved['frequency'] == pytest.approx(200.0)

    def test_matching_config_no_dialog(self, qtbot, device, tmp_path):
        device._frequency = 10.0
        t = self._make_tree(qtbot, device, tmp_path)
        t._configure.save(device)
        with patch('lib.QInstrumentTree.QReconcileDialog') as MockDialog:
            t._restoreSettings()
        MockDialog.assert_not_called()

    def test_mismatch_shows_dialog(self, qtbot, device, tmp_path):
        device._frequency = 10.0
        t = self._make_tree(qtbot, device, tmp_path)
        t._configure.save(device)
        device._frequency = 99.0
        mock_dialog = MagicMock()
        mock_dialog.exec.return_value = True
        mock_dialog.keep_hardware = True
        with patch('lib.QInstrumentTree.QReconcileDialog',
                   return_value=mock_dialog) as MockCls:
            t._restoreSettings()
        MockCls.assert_called_once()

    def test_use_saved_pushes_to_device(self, qtbot, device, tmp_path):
        device._frequency = 10.0
        t = self._make_tree(qtbot, device, tmp_path)
        t._configure.save(device)
        device._frequency = 99.0
        mock_dialog = MagicMock()
        mock_dialog.exec.return_value = True
        mock_dialog.keep_hardware = False
        with patch('lib.QInstrumentTree.QReconcileDialog',
                   return_value=mock_dialog):
            t._restoreSettings()
        assert device._frequency == pytest.approx(10.0)

    def test_dismissed_dialog_keeps_hardware(self, qtbot, device, tmp_path):
        device._frequency = 10.0
        t = self._make_tree(qtbot, device, tmp_path)
        t._configure.save(device)
        device._frequency = 55.0
        mock_dialog = MagicMock()
        mock_dialog.exec.return_value = False
        mock_dialog.keep_hardware = True
        with patch('lib.QInstrumentTree.QReconcileDialog',
                   return_value=mock_dialog):
            t._restoreSettings()
        assert device._frequency == pytest.approx(55.0)

    def test_hardware_dominant_passed_to_dialog(self, qtbot, device, tmp_path):
        device._frequency = 10.0
        t = self._make_tree(qtbot, device, tmp_path)
        t.HARDWARE_DOMINANT = True
        t._configure.save(device)
        device._frequency = 99.0
        mock_dialog = MagicMock()
        mock_dialog.exec.return_value = True
        mock_dialog.keep_hardware = True
        with patch('lib.QInstrumentTree.QReconcileDialog',
                   return_value=mock_dialog) as MockCls:
            t._restoreSettings()
        _, kwargs = MockCls.call_args
        assert kwargs.get('hardware_dominant') is True


# ---------------------------------------------------------------------------
# Threading lifecycle
# ---------------------------------------------------------------------------

class TestThreadLifecycle:

    def test_fake_device_stays_on_main_thread(self, qtbot, device):
        t = QInstrumentTree(device=device)
        qtbot.addWidget(t)
        main_thread = t.thread()
        t._startDeviceThread()
        assert t._thread is None
        assert device.thread() is main_thread

    def test_serial_instrument_moved_to_thread(self, qtbot):
        from QInstrument.lib.QSerialInstrument import QSerialInstrument
        inst = QSerialInstrument()
        t = QInstrumentTree(device=inst)
        qtbot.addWidget(t)
        t._startDeviceThread()
        assert t._thread is not None
        assert t._thread.isRunning()
        assert inst.thread() is t._thread
        t._thread.quit()
        t._thread.wait()

    def test_close_stops_thread(self, qtbot):
        from QInstrument.lib.QSerialInstrument import QSerialInstrument
        inst = QSerialInstrument()
        t = QInstrumentTree(device=inst)
        qtbot.addWidget(t)
        t._startDeviceThread()
        thread = t._thread
        t.close()
        assert not thread.isRunning()

    def test_firstshow_not_repeated(self, qtbot, device, monkeypatch):
        t = QInstrumentTree(device=device)
        qtbot.addWidget(t)
        calls = []
        monkeypatch.setattr(t, '_firstShow', lambda: calls.append(1))
        t._restored = True     # simulate already-shown
        from qtpy.QtGui import QShowEvent
        t.showEvent(QShowEvent())
        assert calls == []
