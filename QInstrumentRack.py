# TODO: Provide methods to search for instruments by type or
#       identification string.
# TODO: Provide methods to rearrange instruments in the rack.
from pathlib import Path

from qtpy import QtWidgets, QtCore
from QInstrument.lib.QInstrumentWidget import QInstrumentWidget
from QInstrument.lib.Configure import Configure
import importlib
import logging


logger = logging.getLogger(__name__)


class _InstrumentSlot(QtWidgets.QWidget):
    '''Wraps one instrument widget with a right-click remove action.'''

    removeRequested = QtCore.Signal(str)

    def __init__(self,
                 name: str,
                 widget: QInstrumentWidget,
                 parent=None) -> None:
        super().__init__(parent)
        self._name = name
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(widget)

    def contextMenuEvent(self, event) -> None:
        menu = QtWidgets.QMenu(self)
        action = menu.addAction(f'Remove {self._name}')
        if menu.exec(event.globalPos()) == action:
            self.removeRequested.emit(self._name)


class _InstrumentPicker(QtWidgets.QDialog):
    '''Dialog for selecting an instrument to add to the rack.'''

    def __init__(self,
                 instruments: list[str],
                 parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle('Add Instrument')
        layout = QtWidgets.QVBoxLayout(self)
        self._list = QtWidgets.QListWidget()
        self._list.addItems(instruments)
        self._list.itemDoubleClicked.connect(self.accept)
        layout.addWidget(self._list)
        BB = QtWidgets.QDialogButtonBox
        buttons = BB(
            BB.StandardButton.Ok | BB.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def selected(self) -> str | None:
        '''Return the selected instrument name, or ``None``.'''
        items = self._list.selectedItems()
        return items[0].text() if items else None


class QInstrumentRack(QtWidgets.QWidget):
    '''A widget that holds multiple instrument widgets in a
    vertical layout.

    The instrument list is persisted to
    ``~/.QInstrument/QInstrumentRack.json`` via :class:`Configure`.
    On first show, if no instruments were supplied at construction,
    the saved list is restored.  On close, the current list is saved.

    Instruments can be added at runtime via the "Add instrument…"
    button.  Right-clicking any instrument opens a context menu with
    a "Remove" action.

    Parameters
    ----------
    parent : QWidget | None
        Parent widget. Default: ``None``.
    instruments : list[str] | None
        Instrument names to load on construction.
        Each name is the bare instrument name without the ``Q``
        prefix or ``Widget`` suffix (e.g. ``'DS345'``).
        Default: ``None`` (empty rack).
    '''

    def __init__(self,
                 parent: QtWidgets.QWidget | None = None,
                 instruments: list[str] | None = None) -> None:
        super().__init__(parent)
        self._instrument_names: list[str] = []
        self._configure = Configure()
        self._shown = False
        self._setupUi()
        self.addInstrumentsByNames(instruments)

    def _setupUi(self) -> None:
        outer = QtWidgets.QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        outer.addWidget(self._makeToolbar())
        self._slots = QtWidgets.QVBoxLayout()
        self._slots.setContentsMargins(0, 0, 0, 0)
        self._slots.setSpacing(0)
        outer.addLayout(self._slots)
        outer.addStretch()

    def _makeToolbar(self) -> QtWidgets.QWidget:
        bar = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(bar)
        layout.setContentsMargins(4, 4, 4, 0)
        btn = QtWidgets.QPushButton('Add instrument\u2026')
        btn.clicked.connect(self._addInstrumentDialog)
        layout.addWidget(btn)
        layout.addStretch()
        return bar

    @property
    def settings(self) -> dict:
        '''dict: instrument list as ``{'instruments': [...]}``.

        Getting returns the names of all currently loaded instruments.
        Setting clears the rack and reloads from the supplied dict.
        '''
        return {'instruments': list(self._instrument_names)}

    @settings.setter
    def settings(self, settings: dict) -> None:
        self.clearInstruments()
        self.addInstrumentsByNames(
            settings.get('instruments', [])
        )

    def addInstrument(self,
                      instrument: QInstrumentWidget,
                      name: str = '') -> None:
        '''Add an instrument widget instance to the rack.

        Parameters
        ----------
        instrument : QInstrumentWidget
            The instrument widget to add.
        name : str
            Display name for the remove context menu.  Derived from
            the widget class name if omitted.
        '''
        if not name:
            cls_name = type(instrument).__name__
            name = (cls_name
                    .removeprefix('Q')
                    .removesuffix('Widget'))
        slot = _InstrumentSlot(name, instrument, self)
        slot.removeRequested.connect(self._removeInstrument)
        self._slots.addWidget(slot)
        self._instrument_names.append(name)

    def addInstruments(self,
                       instruments: list[QInstrumentWidget]
                       ) -> None:
        '''Add multiple instrument widget instances to the rack.

        Parameters
        ----------
        instruments : list[QInstrumentWidget]
            Instrument widget instances to add.
        '''
        for instrument in instruments:
            self.addInstrument(instrument)

    def addInstrumentByName(self, name: str) -> None:
        '''Add an instrument widget by its bare instrument name.

        Searches manufacturer subdirectories under ``instruments/``
        for a package named ``name`` that contains a ``widget.py``,
        then instantiates ``Q<name>Widget``.  Logs a warning and does
        nothing if the instrument or widget class cannot be found.

        Parameters
        ----------
        name : str
            Bare instrument name without the ``Q`` prefix or
            ``Widget`` suffix (e.g. ``'DS345'``).
        '''
        modulename = self._findInstrumentModule(name)
        if modulename is None:
            logger.warning(f"Instrument '{name}' not found.")
            return
        widgetname = f'Q{name}Widget'
        try:
            mod = importlib.import_module(modulename)
            cls = getattr(mod, widgetname)
            instrument = cls()
        except (ModuleNotFoundError, AttributeError) as e:
            logger.warning(
                f"Error loading instrument '{name}': {e}")
            return
        self.addInstrument(instrument, name)

    def addInstrumentsByNames(self,
                               names: list[str] | None) -> None:
        '''Add multiple instruments by their bare names.

        Parameters
        ----------
        names : list[str] | None
            Bare instrument names to load.
            ``None`` is treated as an empty list.
        '''
        for name in (names or []):
            self.addInstrumentByName(name)

    def clearInstruments(self) -> None:
        '''Remove and schedule deletion of all instrument widgets.'''
        self._instrument_names.clear()
        while self._slots.count():
            item = self._slots.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    @classmethod
    def availableInstruments(cls) -> list[str]:
        '''Return names of all instruments that have a widget module.

        Scans the ``instruments/`` directory two levels deep for
        subpackages that contain a ``widget.py`` file.  Instruments
        are organised under manufacturer subdirectories; only the bare
        instrument name is returned.

        Returns
        -------
        list[str]
            Sorted list of bare instrument names.
        '''
        instruments_dir = Path(__file__).parent / 'instruments'
        names = []
        for mfr in instruments_dir.iterdir():
            if not mfr.is_dir() or mfr.name.startswith('_'):
                continue
            for inst in mfr.iterdir():
                if inst.is_dir() and (inst / 'widget.py').exists():
                    names.append(inst.name)
        return sorted(names)

    @classmethod
    def _findInstrumentModule(cls, name: str) -> str | None:
        '''Resolve a bare instrument name to its full module path.

        Searches manufacturer subdirectories under ``instruments/``
        for a directory matching ``name`` that contains a ``widget.py``.

        Parameters
        ----------
        name : str
            Bare instrument name (e.g. ``'DS345'``).

        Returns
        -------
        str | None
            Dotted module path for the widget module, or ``None`` if
            not found.
        '''
        instruments_dir = Path(__file__).parent / 'instruments'
        for mfr in instruments_dir.iterdir():
            if not mfr.is_dir() or mfr.name.startswith('_'):
                continue
            inst = mfr / name
            if inst.is_dir() and (inst / 'widget.py').exists():
                return f'QInstrument.instruments.{mfr.name}.{name}.widget'
        return None

    def _removeInstrument(self, name: str) -> None:
        for i in range(self._slots.count()):
            item = self._slots.itemAt(i)
            slot = item.widget() if item else None
            if slot is not None and slot._name == name:
                self._slots.takeAt(i).widget().deleteLater()
                self._instrument_names.remove(name)
                break

    def _addInstrumentDialog(self) -> None:
        available = self.availableInstruments()
        if not available:
            return
        picker = _InstrumentPicker(available, self)
        DD = QtWidgets.QDialog.DialogCode
        if picker.exec() == DD.Accepted:
            name = picker.selected()
            if name:
                self.addInstrumentByName(name)

    def showEvent(self, event) -> None:
        '''Restore the instrument list on first show.

        On the first show, if no instruments were loaded at
        construction, calls :meth:`Configure.restore` to reload
        the previously saved instrument list.
        '''
        if not self._shown:
            self._shown = True
            if not self._instrument_names:
                self._configure.restore(self)
        super().showEvent(event)

    def closeEvent(self, event) -> None:
        '''Save the instrument list when the widget is closed.

        Persists the current instrument list to
        ``~/.QInstrument/QInstrumentRack.json``.  Only saves if
        the widget was previously shown, so test widgets closed
        during teardown do not overwrite saved configuration.
        '''
        if self._shown:
            self._configure.save(self)
        super().closeEvent(event)

    @classmethod
    def example(cls) -> None:
        '''Display a rack populated with example instruments.'''
        import sys
        from qtpy.QtWidgets import QApplication
        app = QApplication.instance() or QApplication(sys.argv)
        rack = cls(instruments='Proscan DS345 SR830'.split())
        rack.show()
        sys.exit(app.exec())


if __name__ == '__main__':
    QInstrumentRack.example()


__all__ = ['QInstrumentRack']
