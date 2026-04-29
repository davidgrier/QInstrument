import json
import logging
import pytest
from pathlib import Path
from lib.Configure import Configure


@pytest.fixture
def cfg(tmp_path, qtbot):
    return Configure(
        datadir=str(tmp_path / 'data'),
        configdir=str(tmp_path / 'config'))


class SimpleObj:
    '''Object with a settable settings dict for testing save/restore.'''
    def __init__(self, settings=None):
        self._settings = settings or {}

    @property
    def settings(self):
        return self._settings

    @settings.setter
    def settings(self, s):
        self._settings = dict(s)


class EmptyObj:
    @property
    def settings(self):
        return {}

    @settings.setter
    def settings(self, s):
        pass


# ---------------------------------------------------------------------------
# Directory creation
# ---------------------------------------------------------------------------

class TestDirectoryCreation:

    def test_datadir_created_on_init(self, tmp_path, qtbot):
        Configure(datadir=str(tmp_path / 'mydata'),
                  configdir=str(tmp_path / 'mycfg'))
        assert (tmp_path / 'mydata').is_dir()

    def test_configdir_created_on_init(self, tmp_path, qtbot):
        Configure(datadir=str(tmp_path / 'mydata'),
                  configdir=str(tmp_path / 'mycfg'))
        assert (tmp_path / 'mycfg').is_dir()


# ---------------------------------------------------------------------------
# configname
# ---------------------------------------------------------------------------

class TestConfigname:

    def test_uses_class_name(self, cfg):
        assert 'SimpleObj' in cfg.configname(SimpleObj())

    def test_has_json_extension(self, cfg):
        assert cfg.configname(SimpleObj()).endswith('.json')

    def test_resides_in_configdir(self, cfg):
        assert Path(cfg.configname(SimpleObj())).parent == cfg.configdir


# ---------------------------------------------------------------------------
# save
# ---------------------------------------------------------------------------

class TestSave:

    def test_creates_json_file(self, cfg):
        obj = SimpleObj({'freq': 440.0, 'count': 3})
        cfg.save(obj)
        assert Path(cfg.configname(obj)).exists()

    def test_saved_content_matches_settings(self, cfg):
        obj = SimpleObj({'freq': 440.0, 'count': 3})
        cfg.save(obj)
        with open(cfg.configname(obj)) as f:
            data = json.load(f)
        assert data == {'freq': 440.0, 'count': 3}

    def test_no_file_written_when_settings_empty(self, cfg):
        obj = EmptyObj()
        cfg.save(obj)
        assert not Path(cfg.configname(obj)).exists()

    def test_explicit_settings_overrides_obj_settings(self, cfg):
        obj = SimpleObj({'freq': 440.0})
        cfg.save(obj, settings={'freq': 999.0})
        with open(cfg.configname(obj)) as f:
            data = json.load(f)
        assert data == {'freq': 999.0}

    def test_explicit_settings_does_not_read_obj_settings(self, cfg):
        class NeverRead:
            @property
            def settings(self):
                raise AssertionError('obj.settings should not be read')

        obj = NeverRead()
        cfg.save(obj, settings={'x': 1.0})   # must not raise


# ---------------------------------------------------------------------------
# restore
# ---------------------------------------------------------------------------

class TestRestore:

    def test_applies_saved_settings(self, cfg):
        saved = SimpleObj({'freq': 440.0, 'enabled': True})
        cfg.save(saved)
        target = SimpleObj()
        cfg.restore(target)
        assert target._settings == {'freq': 440.0, 'enabled': True}

    def test_logs_warning_when_file_missing(self, cfg, caplog):
        with caplog.at_level(logging.WARNING):
            cfg.restore(SimpleObj())     # no prior save — file does not exist
        assert 'Could not read' in caplog.text


# ---------------------------------------------------------------------------
# read
# ---------------------------------------------------------------------------

class TestRead:

    def test_returns_none_when_file_missing(self, cfg):
        assert cfg.read(SimpleObj()) is None

    def test_returns_saved_dict_when_file_exists(self, cfg):
        obj = SimpleObj({'freq': 440.0, 'enabled': True})
        cfg.save(obj)
        result = cfg.read(obj)
        assert result == {'freq': 440.0, 'enabled': True}

    def test_returns_none_on_malformed_json(self, cfg):
        obj = SimpleObj({'x': 1.0})
        path = cfg.configname(obj)
        with open(path, 'w') as f:
            f.write('not valid json {{{')
        assert cfg.read(obj) is None

    def test_does_not_apply_settings_to_object(self, cfg):
        saved = SimpleObj({'freq': 440.0})
        cfg.save(saved)
        target = SimpleObj({'freq': 0.0})
        cfg.read(target)
        assert target._settings == {'freq': 0.0}


# ---------------------------------------------------------------------------
# filename / timestamp
# ---------------------------------------------------------------------------

class TestFilename:

    def test_result_is_under_datadir(self, cfg):
        assert Path(cfg.filename('test')).parent == cfg.datadir

    def test_starts_with_prefix(self, cfg):
        assert Path(cfg.filename('myprefix')).name.startswith('myprefix')

    def test_ends_with_suffix(self, cfg):
        assert cfg.filename('pre', suffix='.csv').endswith('.csv')

    def test_timestamp_is_nonempty_string(self, cfg):
        ts = cfg.timestamp()
        assert isinstance(ts, str) and len(ts) > 0
