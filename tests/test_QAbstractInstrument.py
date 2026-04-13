import logging
import pytest
from lib.QAbstractInstrument import QAbstractInstrument


class SimpleInstrument(QAbstractInstrument):
    '''Minimal concrete instrument for testing.'''
    def transmit(self, data): pass
    def receive(self, **kwargs): return ''


@pytest.fixture
def inst(qtbot):
    return SimpleInstrument()


# ---------------------------------------------------------------------------
# registerProperty — _AUTO convention
# ---------------------------------------------------------------------------

class TestRegisterPropertyAuto:

    def test_auto_getter_reads_backing_attribute(self, inst):
        inst._speed = 42.0
        inst.registerProperty('speed')
        assert inst.get('speed') == 42.0

    def test_auto_setter_writes_backing_attribute(self, inst):
        inst._speed = 0.0
        inst.registerProperty('speed')
        inst.set('speed', 99.0)
        assert inst._speed == 99.0

    def test_auto_setter_coerces_to_ptype(self, inst):
        inst._count = 0
        inst.registerProperty('count', ptype=int)
        inst.set('count', 3.9)
        assert inst._count == 3

    def test_auto_setter_coerces_bool(self, inst):
        inst._flag = False
        inst.registerProperty('flag', ptype=bool)
        inst.set('flag', 1)
        assert inst._flag is True


# ---------------------------------------------------------------------------
# registerProperty — explicit callables
# ---------------------------------------------------------------------------

class TestRegisterPropertyExplicit:

    def test_explicit_getter_called(self, inst):
        inst.registerProperty('pi', getter=lambda: 3.14)
        assert inst.get('pi') == 3.14

    def test_explicit_setter_called(self, inst):
        store = {}
        inst.registerProperty('x',
                               getter=lambda: store.get('x', 0.),
                               setter=lambda v: store.__setitem__('x', v))
        inst.set('x', 7.0)
        assert store['x'] == 7.0

    def test_read_only_setter_none_logs_warning(self, inst, caplog):
        inst.registerProperty('ro', getter=lambda: 1.0, setter=None)
        with caplog.at_level(logging.WARNING):
            inst.set('ro', 2.0)
        assert 'read-only' in caplog.text

    def test_read_only_value_unchanged(self, inst):
        store = [1.0]
        inst.registerProperty('ro',
                               getter=lambda: store[0],
                               setter=None)
        inst.set('ro', 9.0)
        assert store[0] == 1.0

    def test_overwrite_replaces_previous_registration(self, inst):
        inst.registerProperty('val', getter=lambda: 1.0)
        inst.registerProperty('val', getter=lambda: 2.0)
        assert inst.get('val') == 2.0


# ---------------------------------------------------------------------------
# get / set — error handling
# ---------------------------------------------------------------------------

class TestGetSet:

    def test_get_unknown_logs_error(self, inst, caplog):
        with caplog.at_level(logging.ERROR):
            result = inst.get('nonexistent')
        assert result is None
        assert 'nonexistent' in caplog.text

    def test_set_unknown_logs_error(self, inst, caplog):
        with caplog.at_level(logging.ERROR):
            inst.set('nonexistent', 1.0)
        assert 'nonexistent' in caplog.text

    def test_properties_list_reflects_registered_names(self, inst):
        inst.registerProperty('a', getter=lambda: 1)
        inst.registerProperty('b', getter=lambda: 2)
        assert 'a' in inst.properties
        assert 'b' in inst.properties


# ---------------------------------------------------------------------------
# propertyValue signal
# ---------------------------------------------------------------------------

class TestPropertyValueSignal:

    def test_get_emits_signal(self, inst, qtbot):
        inst.registerProperty('v', getter=lambda: 5.0)
        with qtbot.waitSignal(inst.propertyValue, timeout=500) as blocker:
            inst.get('v')
        assert blocker.args == ['v', 5.0]

    def test_set_emits_signal(self, inst, qtbot):
        store = [0.0]
        inst.registerProperty('v',
                               getter=lambda: store[0],
                               setter=lambda v: store.__setitem__(0, v))
        with qtbot.waitSignal(inst.propertyValue, timeout=500) as blocker:
            inst.set('v', 3.0)
        assert blocker.args == ['v', 3.0]


# ---------------------------------------------------------------------------
# settings
# ---------------------------------------------------------------------------

class TestSettings:

    def test_settings_returns_all_values(self, inst):
        inst.registerProperty('a', getter=lambda: 1.0)
        inst.registerProperty('b', getter=lambda: 2.0)
        s = inst.settings
        assert s['a'] == 1.0
        assert s['b'] == 2.0

    def test_settings_excludes_readonly_properties(self, inst):
        inst.registerProperty('rw', getter=lambda: 1.0, setter=lambda v: None)
        inst.registerProperty('ro', getter=lambda: 2.0, setter=None)
        assert 'rw' in inst.settings
        assert 'ro' not in inst.settings

    def test_settings_excludes_non_persistent_properties(self, inst):
        inst.registerProperty('keep', getter=lambda: 1.0,
                               setter=lambda v: None, persist=True)
        inst.registerProperty('skip', getter=lambda: 2.0,
                               setter=lambda v: None, persist=False)
        assert 'keep' in inst.settings
        assert 'skip' not in inst.settings

    def test_settings_setter_applies_values(self, inst):
        store = {'a': 0.0, 'b': 0.0}
        inst.registerProperty('a',
                               getter=lambda: store['a'],
                               setter=lambda v: store.__setitem__('a', v))
        inst.registerProperty('b',
                               getter=lambda: store['b'],
                               setter=lambda v: store.__setitem__('b', v))
        inst.settings = {'a': 10.0, 'b': 20.0}
        assert store == {'a': 10.0, 'b': 20.0}

    def test_settings_setter_skips_unknown_keys(self, inst):
        inst.registerProperty('a', getter=lambda: 1.0, setter=lambda v: None)
        inst.settings = {'a': 1.0, 'bogus': 99.0}  # must not raise

    def test_settings_setter_ignores_non_persistent_keys(self, inst):
        store = [0.0]
        inst.registerProperty('transient',
                               getter=lambda: store[0],
                               setter=lambda v: store.__setitem__(0, v),
                               persist=False)
        inst.settings = {'transient': 99.0}
        assert store[0] == 0.0  # setter must not have been called


# ---------------------------------------------------------------------------
# registerMethod / execute
# ---------------------------------------------------------------------------

class TestMethods:

    def test_execute_calls_method(self, inst):
        called = []
        inst.registerMethod('go', lambda: called.append(True))
        inst.execute('go')
        assert called == [True]

    def test_execute_unknown_logs_error(self, inst, caplog):
        with caplog.at_level(logging.ERROR):
            inst.execute('missing')
        assert 'missing' in caplog.text

    def test_methods_list_reflects_registered_names(self, inst):
        inst.registerMethod('reset', lambda: None)
        assert 'reset' in inst.methods


# ---------------------------------------------------------------------------
# propertyMeta
# ---------------------------------------------------------------------------

class TestPropertyMeta:

    def test_returns_ptype_and_extra_meta(self, inst):
        inst.registerProperty('speed', getter=lambda: 0.,
                               ptype=float, minimum=0., maximum=100.)
        meta = inst.propertyMeta('speed')
        assert meta['ptype'] is float
        assert meta['minimum'] == pytest.approx(0.)
        assert meta['maximum'] == pytest.approx(100.)

    def test_excludes_getter_and_setter(self, inst):
        inst.registerProperty('speed', getter=lambda: 0.,
                               setter=lambda v: None)
        meta = inst.propertyMeta('speed')
        assert 'getter' not in meta
        assert 'setter' not in meta

    def test_returns_empty_dict_for_unknown_property(self, inst):
        assert inst.propertyMeta('nonexistent') == {}

    def test_debounce_value_round_trips(self, inst):
        inst.registerProperty('power', getter=lambda: 0., debounce=500)
        assert inst.propertyMeta('power')['debounce'] == 500


# ---------------------------------------------------------------------------
# getValue / handshake / expect helpers
# ---------------------------------------------------------------------------

class TestHelpers:

    def test_getValue_converts_response(self, inst, monkeypatch):
        monkeypatch.setattr(inst, 'receive', lambda **kw: '3.14')
        result = inst.getValue('FREQ?', float)
        assert result == pytest.approx(3.14)

    def test_getValue_returns_none_on_conversion_failure(self, inst, monkeypatch):
        monkeypatch.setattr(inst, 'receive', lambda **kw: 'bad')
        assert inst.getValue('FREQ?', float) is None

    def test_expect_returns_true_when_response_matches(self, inst, monkeypatch):
        monkeypatch.setattr(inst, 'receive', lambda **kw: 'DS345')
        assert inst.expect('*IDN?', 'DS345') is True

    def test_expect_returns_false_when_response_does_not_match(
            self, inst, monkeypatch):
        monkeypatch.setattr(inst, 'receive', lambda **kw: 'OTHER')
        assert inst.expect('*IDN?', 'DS345') is False
