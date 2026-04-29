import pytest
from lib.QFakeInstrument import QFakeInstrument


# ---------------------------------------------------------------------------
# Helpers — minimal subclasses
# ---------------------------------------------------------------------------

class RegisteredFake(QFakeInstrument):
    '''New-style: uses _registerProperties via auto-call.'''
    def _registerProperties(self):
        self._register('frequency', 'FREQ', float)
        self._register('enabled',   'ENAB', bool)
        self._register('count',     'CNTR', int)


class OldStyleFake(QFakeInstrument):
    '''Old-style: registers properties manually in __init__.'''
    def __init__(self):
        super().__init__()
        self._value = 0.0
        self.registerProperty('value')


# ---------------------------------------------------------------------------
# Basic contract
# ---------------------------------------------------------------------------

class TestContract:

    def test_isOpen_returns_true(self, qtbot):
        f = QFakeInstrument()
        assert f.isOpen() is True

    def test_transmit_is_noop(self, qtbot):
        f = QFakeInstrument()
        f.transmit('FREQ?')          # must not raise

    def test_receive_returns_empty_string(self, qtbot):
        f = QFakeInstrument()
        assert f.receive() == ''

    def test_identification_includes_class_name(self, qtbot):
        f = RegisteredFake()
        assert 'RegisteredFake' in f.identification


# ---------------------------------------------------------------------------
# _register — in-memory store
# ---------------------------------------------------------------------------

class TestRegister:

    def test_float_property_default_is_zero(self, qtbot):
        f = RegisteredFake()
        assert f.get('frequency') == 0.0

    def test_bool_property_default_is_false(self, qtbot):
        f = RegisteredFake()
        assert f.get('enabled') is False

    def test_int_property_default_is_zero(self, qtbot):
        f = RegisteredFake()
        assert f.get('count') == 0

    def test_set_and_get_roundtrip(self, qtbot):
        f = RegisteredFake()
        f.set('frequency', 1000.0)
        assert f.get('frequency') == 1000.0

    def test_dtype_coercion_on_set(self, qtbot):
        f = RegisteredFake()
        f.set('count', 3.9)          # float -> int
        assert f.get('count') == 3

    def test_bool_coercion_on_set(self, qtbot):
        f = RegisteredFake()
        f.set('enabled', 1)
        assert f.get('enabled') is True

    def test_independent_store_per_instance(self, qtbot):
        a = RegisteredFake()
        b = RegisteredFake()
        a.set('frequency', 500.0)
        assert b.get('frequency') == 0.0

    def test_all_registered_properties_present(self, qtbot):
        f = RegisteredFake()
        assert set(['frequency', 'enabled', 'count']).issubset(f.properties)


# ---------------------------------------------------------------------------
# Auto-call of _registerProperties / _registerMethods
# ---------------------------------------------------------------------------

class TestAutoRegister:

    def test_properties_available_without_explicit_init(self, qtbot):
        f = RegisteredFake()
        assert 'frequency' in f.properties

    def test_methods_auto_registered(self, qtbot):
        called = []

        class WithMethods(QFakeInstrument):
            def _registerProperties(self):
                self._register('x', 'X')
            def _registerMethods(self):
                self.registerMethod('reset', lambda: called.append(True))

        f = WithMethods()
        assert 'reset' in f.methods
        f.execute('reset')
        assert called == [True]

    def test_no_auto_call_without_register_method(self, qtbot):
        # QFakeInstrument with no _registerProperties should not raise
        f = QFakeInstrument()
        assert f.properties == []


# ---------------------------------------------------------------------------
# Old-style backward compatibility
# ---------------------------------------------------------------------------

class TestOldStyle:

    def test_manual_property_accessible(self, qtbot):
        f = OldStyleFake()
        assert 'value' in f.properties

    def test_auto_getter_reads_backing_attribute(self, qtbot):
        f = OldStyleFake()
        f._value = 7.0
        assert f.get('value') == 7.0

    def test_auto_setter_writes_backing_attribute(self, qtbot):
        f = OldStyleFake()
        f.set('value', 3.5)
        assert f._value == 3.5
