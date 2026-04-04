import inspect
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from lib.QInstrumentWidget import QInstrumentWidget


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
