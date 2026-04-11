# TODO: Provide methods to search for instruments by type or
#       identification string.
from pathlib import Path

from qtpy import QtWidgets, QtCore, QtGui
from QInstrument.lib.QInstrumentWidget import QInstrumentWidget
from QInstrument.lib.Configure import Configure
import importlib
import logging


logger = logging.getLogger(__name__)


class _DragHandle(QtWidgets.QLabel):
    '''Grip widget that initiates instrument slot reordering.

    Displays a vertical ellipsis (⋮) and changes the cursor to a
    closed-hand shape while the left button is held.  Emits
    :attr:`dragging` on every mouse-move during a drag so the rack
    can highlight the current drop target, and emits :attr:`dropped`
    on release so the rack can commit the move.

    Signals
    -------
    dragging(QtCore.QPoint)
        Emitted continuously during a left-button drag with the
        current global cursor position.
    dropped(QtCore.QPoint)
        Emitted on left-button release with the global cursor position
        at the moment of release.
    '''

    dropped = QtCore.Signal(QtCore.QPoint)
    dragging = QtCore.Signal(QtCore.QPoint)

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__('\u22ee', parent)
        self.setFixedWidth(14)
        self.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.setCursor(QtCore.Qt.CursorShape.OpenHandCursor)

    def mousePressEvent(self, event: QtCore.QEvent) -> None:
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            self.setCursor(QtCore.Qt.CursorShape.ClosedHandCursor)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QtCore.QEvent) -> None:
        if event.buttons() & QtCore.Qt.MouseButton.LeftButton:
            self.dragging.emit(QtGui.QCursor.pos())
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QtCore.QEvent) -> None:
        self.setCursor(QtCore.Qt.CursorShape.OpenHandCursor)
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            self.dropped.emit(QtGui.QCursor.pos())
        super().mouseReleaseEvent(event)


class _InstrumentSlot(QtWidgets.QWidget):
    '''Wraps one instrument widget with a drag handle and close button.

    Layout (left to right): ⋮ drag handle | instrument widget.
    The × close button and a drop-target indicator are overlaid
    absolutely so they do not affect the horizontal layout.

    The close button and drag handle are shown only when the slot is
    editable (see :meth:`setEditable`).  The drop-target indicator —
    a 3 px coloured bar across the top of the slot — is shown only
    while another slot is being dragged over this one.

    Signals
    -------
    removeRequested(str)
        Emitted when the × button is clicked, carrying the slot name.
    dropRequested(object, QtCore.QPoint)
        Emitted on drag release, carrying this slot and the global
        drop position.
    hoverRequested(object, QtCore.QPoint)
        Emitted continuously during a drag, carrying this slot and the
        current global cursor position.
    '''

    removeRequested = QtCore.Signal(str)
    dropRequested = QtCore.Signal(object, QtCore.QPoint)
    hoverRequested = QtCore.Signal(object, QtCore.QPoint)

    def __init__(self,
                 name: str,
                 widget: QInstrumentWidget,
                 parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self._name = name
        self._setupUi(widget)
        self._connectSignals()

    def _setupUi(self, widget: QInstrumentWidget) -> None:
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self._handle = _DragHandle(self)
        layout.addWidget(self._handle)
        layout.addWidget(widget)
        self._closeButton = QtWidgets.QPushButton('\u00d7', self)
        self._closeButton.setFixedSize(18, 18)
        self._closeButton.setFlat(True)
        self._dropIndicator = QtWidgets.QFrame(self)
        self._dropIndicator.setFixedHeight(3)
        self._dropIndicator.setStyleSheet('background: palette(highlight);')
        self._dropIndicator.setVisible(False)

    def _connectSignals(self) -> None:
        self._closeButton.clicked.connect(
            lambda: self.removeRequested.emit(self._name))
        self._handle.dropped.connect(
            lambda pos: self.dropRequested.emit(self, pos))
        self._handle.dragging.connect(
            lambda pos: self.hoverRequested.emit(self, pos))

    def setEditable(self, editable: bool) -> None:
        '''Show or hide the drag handle and close button.

        Parameters
        ----------
        editable : bool
            ``True`` to show edit controls; ``False`` to hide them.
        '''
        self._handle.setVisible(editable)
        self._closeButton.setVisible(editable)

    def setHighlighted(self, highlighted: bool) -> None:
        '''Show or hide the drop-target indicator.

        The indicator is a 3 px bar in the system highlight colour
        across the top of the slot.  It is shown while another slot's
        drag handle is held over this slot and cleared on release.

        Parameters
        ----------
        highlighted : bool
            ``True`` to show the indicator; ``False`` to hide it.
        '''
        self._dropIndicator.setVisible(highlighted)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        btn = self._closeButton
        btn.move(self.width() - btn.width() - 2, 2)
        btn.raise_()
        self._dropIndicator.resize(self.width(), 3)
        self._dropIndicator.move(0, 0)
        self._dropIndicator.raise_()


class _InstrumentPicker(QtWidgets.QDialog):
    '''Dialog for selecting an instrument to add to the rack.'''

    def __init__(self,
                 instruments: list[str],
                 parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self._setupUi(instruments)
        self._connectSignals()

    def _setupUi(self, instruments: list[str]) -> None:
        self.setWindowTitle('Add Instrument')
        layout = QtWidgets.QVBoxLayout(self)
        self._list = QtWidgets.QListWidget()
        self._list.addItems(instruments)
        layout.addWidget(self._list)
        ok = QtWidgets.QDialogButtonBox.StandardButton.Ok
        cancel = QtWidgets.QDialogButtonBox.StandardButton.Cancel
        self._buttons = QtWidgets.QDialogButtonBox(ok | cancel)
        layout.addWidget(self._buttons)

    def _connectSignals(self) -> None:
        self._list.itemDoubleClicked.connect(self.accept)
        self._buttons.accepted.connect(self.accept)
        self._buttons.rejected.connect(self.reject)

    def selected(self) -> str | None:
        '''Return the selected instrument name, or ``None``.'''
        items = self._list.selectedItems()
        return items[0].text() if items else None


class QInstrumentRack(QtWidgets.QWidget):
    '''A widget that holds multiple instrument widgets in a vertical layout.

    The instrument list is persisted to
    ``~/.QInstrument/QInstrumentRack.json`` via :class:`Configure`.
    On first show, if no instruments were supplied at construction,
    the saved list is restored.  On close, the current list is saved.

    When :attr:`editable` is ``True`` (the default), the rack provides:

    - An "Add instrument…" toolbar button that opens a picker dialog
      listing all instruments found under ``instruments/``.
    - A × close button overlaid on each slot to remove that instrument.
    - A ⋮ drag handle on each slot.  Dragging highlights the target
      slot with a coloured bar and moves the dragged slot to that
      position on release.

    Set :attr:`editable` to ``False`` to hide all of the above, for
    example when embedding the rack in an application where the
    instrument set should be fixed.

    Parameters
    ----------
    parent : QWidget | None
        Parent widget. Default: ``None``.
    instruments : list[str] | None
        Instrument names to load on construction.
        Each name is the bare instrument name without the ``Q``
        prefix or ``Widget`` suffix (e.g. ``'DS345'``).
        Default: ``None`` (empty rack).
    editable : bool
        If ``False``, the toolbar, drag handles, and close buttons
        are all hidden. Default: ``True``.
    fake : bool
        If ``True``, all instruments — including those added later
        via the "Add instrument…" dialog — use fake devices instead
        of probing for real hardware.  Default: ``False``.
    '''

    def __init__(self,
                 parent: QtWidgets.QWidget | None = None,
                 instruments: list[str] | None = None,
                 editable: bool = True,
                 fake: bool = False) -> None:
        super().__init__(parent)
        self._configure = Configure()
        self._shown = False
        self._editable = editable
        self._fake = fake
        self._setupUi()
        self.addInstrumentsByNames(instruments, fake=fake)

    def _setupUi(self) -> None:
        outer = QtWidgets.QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        self._toolbar = self._makeToolbar()
        self._toolbar.setVisible(self._editable)
        outer.addWidget(self._toolbar)
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

    def _slotAt(self, index: int) -> '_InstrumentSlot | None':
        item = self._slots.itemAt(index)
        return item.widget() if item else None

    def _iterSlots(self):
        for i in range(self._slots.count()):
            if slot := self._slotAt(i):
                yield slot

    @property
    def settings(self) -> dict:
        '''dict: instrument list as ``{'instruments': [...]}``.

        Getting returns instrument names in their current display order,
        preserving any reordering done by dragging.
        Setting clears the rack and reloads from the supplied dict.
        '''
        names = [slot._name for slot in self._iterSlots()]
        return {'instruments': names}

    @settings.setter
    def settings(self, settings: dict) -> None:
        self.clearInstruments()
        self.addInstrumentsByNames(settings.get('instruments', []))

    @property
    def editable(self) -> bool:
        '''bool: whether the user can add, remove, or reorder instruments.

        When ``False``, the toolbar, drag handles, and close buttons
        are all hidden. Defaults to ``True``.
        '''
        return self._editable

    @editable.setter
    def editable(self, value: bool) -> None:
        self._editable = value
        self._toolbar.setVisible(value)
        for slot in self._iterSlots():
            slot.setEditable(value)

    def addInstrument(self,
                      instrument: QInstrumentWidget,
                      name: str = '') -> None:
        '''Add an instrument widget instance to the rack.

        Parameters
        ----------
        instrument : QInstrumentWidget
            The instrument widget to add.
        name : str
            Display name. Derived from the widget class name if omitted.
        '''
        if not name:
            cls_name = type(instrument).__name__
            name = (cls_name
                    .removeprefix('Q')
                    .removesuffix('Widget'))
        slot = _InstrumentSlot(name, instrument, self)
        slot.removeRequested.connect(self._removeInstrument)
        slot.dropRequested.connect(self._moveSlot)
        slot.hoverRequested.connect(self._hoverSlot)
        slot.setEditable(self._editable)
        self._slots.addWidget(slot)
        self.adjustSize()

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

    def addInstrumentByName(self, name: str, fake: bool = False) -> None:
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
        fake : bool
            If ``True``, instantiate the widget with its fake device
            (from the sibling ``fake.py``) instead of probing for
            real hardware.  The widget will be fully enabled.
            Falls back to normal instantiation if no fake is available.
            Default: ``False``.
        '''
        modulename = self._findInstrumentModule(name)
        if modulename is None:
            logger.warning(f"Instrument '{name}' not found.")
            return
        widgetname = f'Q{name}Widget'
        try:
            mod = importlib.import_module(modulename)
            cls = getattr(mod, widgetname)
            if fake:
                fake_cls = cls._fakeCls()
                if fake_cls is not None:
                    instrument = cls(device=fake_cls())
                else:
                    logger.warning(
                        f"No fake available for '{name}'; loading normally.")
                    instrument = cls()
            else:
                instrument = cls()
        except (ModuleNotFoundError, AttributeError) as e:
            logger.warning(
                f"Error loading instrument '{name}': {e}")
            return
        self.addInstrument(instrument, name)

    def addInstrumentsByNames(self,
                              names: list[str] | None,
                              fake: bool = False) -> None:
        '''Add multiple instruments by their bare names.

        Parameters
        ----------
        names : list[str] | None
            Bare instrument names to load.
            ``None`` is treated as an empty list.
        fake : bool
            Passed to :meth:`addInstrumentByName` for each name.
            Default: ``False``.
        '''
        for name in (names or []):
            self.addInstrumentByName(name, fake=fake)

    def clearInstruments(self) -> None:
        '''Remove and schedule deletion of all instrument widgets.'''
        while self._slots.count():
            item = self._slots.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    @classmethod
    def _instrumentPaths(cls):
        '''Yield ``(manufacturer, instrument_name)`` for all widget packages.

        Scans ``instruments/`` two levels deep for subdirectories that
        contain a ``widget.py``.
        '''
        instruments_dir = Path(__file__).parent / 'instruments'
        for mfr in instruments_dir.iterdir():
            if not mfr.is_dir() or mfr.name.startswith('_'):
                continue
            for inst in mfr.iterdir():
                if inst.is_dir() and (inst / 'widget.py').exists():
                    yield mfr.name, inst.name

    @classmethod
    def availableInstruments(cls) -> list[str]:
        '''Return names of all instruments that have a widget module.

        Returns
        -------
        list[str]
            Sorted list of bare instrument names.
        '''
        return sorted(name for _, name in cls._instrumentPaths())

    @classmethod
    def _findInstrumentModule(cls, name: str) -> str | None:
        '''Resolve a bare instrument name to its full module path.

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
        return next(
            (f'QInstrument.instruments.{mfr}.{name}.widget'
             for mfr, inst in cls._instrumentPaths() if inst == name),
            None)

    def _removeInstrument(self, name: str) -> None:
        for i in range(self._slots.count()):
            if (slot := self._slotAt(i)) is not None and slot._name == name:
                self._slots.takeAt(i).widget().deleteLater()
                self.adjustSize()
                break

    def _hoverSlot(self,
                   slot: '_InstrumentSlot',
                   hover_pos: QtCore.QPoint) -> None:
        '''Highlight the slot under the cursor during a drag.

        Connected to each slot's :attr:`hoverRequested` signal.
        Hit-tests all slot geometries against *hover_pos* and calls
        :meth:`_InstrumentSlot.setHighlighted` accordingly, skipping
        the slot being dragged.

        Parameters
        ----------
        slot : _InstrumentSlot
            The slot whose drag handle is being held.
        hover_pos : QtCore.QPoint
            Current global cursor position.
        '''
        local_pos = self.mapFromGlobal(hover_pos)
        target = next(
            (w for w in self._iterSlots() if w.geometry().contains(local_pos)),
            None)
        for s in self._iterSlots():
            s.setHighlighted(s is target and s is not slot)

    def _moveSlot(self,
                  slot: '_InstrumentSlot',
                  drop_pos: QtCore.QPoint) -> None:
        '''Move *slot* to the position of the slot under the drop point.

        Connected to each slot's :attr:`dropRequested` signal.
        Clears all highlights, then hit-tests slot geometries against
        *drop_pos*.  If a different slot is found at that position,
        removes *slot* from the layout and inserts it at the target's
        index using :meth:`QVBoxLayout.removeWidget` /
        :meth:`QVBoxLayout.insertWidget` — no ownership transfer or
        reparenting occurs.

        Parameters
        ----------
        slot : _InstrumentSlot
            The slot to move.
        drop_pos : QtCore.QPoint
            Global cursor position at the moment of release.
        '''
        for s in self._iterSlots():
            s.setHighlighted(False)
        local_pos = self.mapFromGlobal(drop_pos)
        target = next(
            (w for w in self._iterSlots() if w.geometry().contains(local_pos)),
            None)
        if target is None or target is slot:
            return
        target_index = self._slots.indexOf(target)
        self._slots.removeWidget(slot)
        self._slots.insertWidget(target_index, slot)

    def _addInstrumentDialog(self) -> None:
        available = self.availableInstruments()
        if not available:
            return
        picker = _InstrumentPicker(available, self)
        DD = QtWidgets.QDialog.DialogCode
        if picker.exec() == DD.Accepted:
            name = picker.selected()
            if name:
                self.addInstrumentByName(name, fake=self._fake)

    def showEvent(self, event) -> None:
        '''Restore the instrument list on first show.

        On the first show, if no instruments were loaded at
        construction, calls :meth:`Configure.restore` to reload
        the previously saved instrument list.
        '''
        if not self._shown:
            self._shown = True
            if not self._slots.count():
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
        '''Display a rack populated with example instruments.

        Accepts ``-f`` / ``--fake`` on the command line to load fake
        devices instead of probing for real hardware.
        '''
        import sys
        import argparse
        from qtpy.QtWidgets import QApplication
        parser = argparse.ArgumentParser()
        parser.add_argument('-f', '--fake', action='store_true',
                            help='use fake instruments')
        args, _ = parser.parse_known_args()
        app = QApplication.instance() or QApplication(sys.argv)
        rack = cls(instruments='Proscan DS345 SR830'.split(), fake=args.fake)
        rack.show()
        sys.exit(app.exec())


if __name__ == '__main__':
    QInstrumentRack.example()


__all__ = ['QInstrumentRack']
