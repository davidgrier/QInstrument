import logging
from qtpy import QtCore

try:
    from pyqtgraph.parametertree import Parameter, ParameterTree
except ImportError as exc:
    raise ImportError(
        "pyqtgraph is required for QInstrumentTree. "
        "Install it with: pip install 'QInstrument[tree]'"
    ) from exc

logger = logging.getLogger(__name__)

_PTYPE_MAP: dict[type, str] = {
    float: 'float',
    int:   'int',
    bool:  'bool',
    str:   'str',
}


class QInstrumentTree(ParameterTree):
    '''ParameterTree that auto-builds from a QAbstractInstrument.

    The tree is constructed at runtime from the device's property registry.
    Property metadata (``ptype``, ``minimum``, ``maximum``, ``step``)
    registered via :meth:`registerProperty` maps directly to pyqtgraph
    parameter types and constraints.  Read-only properties (``setter=None``)
    appear as non-editable display items.  Registered methods appear as
    action buttons.

    No ``.ui`` file is needed.  Subclass this for each instrument and
    declare :attr:`INSTRUMENT`:

    .. code-block:: python

        class QDS345Tree(QInstrumentTree):
            INSTRUMENT = QDS345

    When ``device`` is not supplied to ``__init__``, the base class
    calls ``INSTRUMENT().find()`` automatically.  Pass an explicit
    ``device`` to override (e.g. to inject a fake for testing).

    Class Attributes
    ----------------
    INSTRUMENT : type | None
        The concrete instrument class to instantiate and search for when
        no ``device`` is supplied.  Must be a :class:`QSerialInstrument`
        subclass (or any class whose no-arg constructor returns an object
        with a ``find()`` method).  ``None`` means no auto-instantiation.

    Parameters
    ----------
    device : QAbstractInstrument, optional
        Instrument to display.  When omitted and :attr:`INSTRUMENT` is
        set, the instrument is located via ``INSTRUMENT().find()``.
    '''

    INSTRUMENT: type | None = None

    def __init__(self, *args, device=None, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._device = None
        self._params: dict[str, Parameter] = {}
        self._updating: bool = False
        if device is None and self.INSTRUMENT is not None:
            device = self.INSTRUMENT().find()
        self.device = device

    @property
    def device(self):
        '''QAbstractInstrument: instrument bound to this tree.

        Setting this property builds the parameter tree from the
        device's registered properties and methods, syncs current
        values if the device is open, and connects signals.  Setting
        to ``None`` is a no-op.  The tree is disabled if the device
        is not open.
        '''
        return self._device

    @device.setter
    def device(self, device) -> None:
        if device is None:
            return
        self._device = device
        self._buildTree()
        if device.isOpen():
            self._syncProperties()
            self._connectSignals()
        else:
            self.setEnabled(False)

    def _buildTree(self) -> None:
        '''Build the parameter tree from the device's registered properties and methods.

        Each registered property becomes a typed parameter (``float``,
        ``int``, ``bool``, or ``str``).  Metadata ``minimum``/``maximum``
        are mapped to parameter limits; ``step`` is forwarded directly.
        Read-only properties are rendered non-editable.  Each registered
        method becomes an ``action`` parameter (button).  The root group
        is labelled with the instrument class name.
        '''
        self._params = {}
        children = []

        for name in self._device.properties:
            meta = self._device.propertyMeta(name)
            ptype = meta.get('ptype', float)
            pg_type = _PTYPE_MAP.get(ptype, 'str')
            readonly = meta.get('readonly', False)
            value = ptype() if ptype in _PTYPE_MAP else ''

            kw: dict = dict(name=name, type=pg_type, value=value,
                            readonly=readonly)
            if not readonly and pg_type in ('float', 'int'):
                if 'minimum' in meta and 'maximum' in meta:
                    kw['limits'] = (meta['minimum'], meta['maximum'])
                if 'step' in meta:
                    kw['step'] = meta['step']
            children.append(kw)

        for name in self._device.methods:
            children.append(dict(name=name, type='action'))

        root = Parameter.create(
            name=type(self._device).__name__,
            type='group',
            children=children,
        )
        self._params = {
            name: root.child(name)
            for name in self._device.properties + self._device.methods
        }
        self.setParameters(root, showTop=True)

    def _syncProperties(self) -> None:
        '''Read each registered property from the device and update the tree.

        Signals are suppressed during the update to avoid triggering
        device writes.
        '''
        self._updating = True
        try:
            for name in self._device.properties:
                value = self._device.get(name)
                if value is not None and name in self._params:
                    try:
                        self._params[name].setValue(value)
                    except Exception:
                        logger.debug(f'Could not sync {name!r} = {value!r}')
        finally:
            self._updating = False

    def _connectSignals(self) -> None:
        '''Connect parameter signals to the device and device signals to the tree.

        Each writable property's ``sigValueChanged`` is wired to
        :meth:`_onParamChanged`.  Each method's ``sigActivated`` calls
        :meth:`device.execute`.  The device's ``propertyValue`` signal
        is wired to :meth:`_onDevicePropertyValue` so that external
        device changes (e.g. polling) are reflected in the tree.
        '''
        for name in self._device.properties:
            meta = self._device.propertyMeta(name)
            if not meta.get('readonly', False):
                self._params[name].sigValueChanged.connect(
                    lambda p, v, n=name: self._onParamChanged(n, v))

        for name in self._device.methods:
            self._params[name].sigActivated.connect(
                lambda p, n=name: self._device.execute(n))

        self._device.propertyValue.connect(self._onDevicePropertyValue)

    def _onParamChanged(self, name: str, value) -> None:
        '''Send a tree-initiated value change to the device.

        Guarded by :attr:`_updating` to prevent re-entrant updates when
        the device echoes the change back via ``propertyValue``.

        Parameters
        ----------
        name : str
            Registered property name.
        value :
            New value from the parameter widget.
        '''
        if self._updating:
            return
        self._updating = True
        try:
            self._device.set(name, value)
        finally:
            self._updating = False

    @QtCore.Slot(str, object)
    def _onDevicePropertyValue(self, name: str, value) -> None:
        '''Update the tree when the device reports a new property value.

        Connected to :attr:`device.propertyValue`.  Guarded by
        :attr:`_updating` to avoid feedback loops with
        :meth:`_onParamChanged`.

        Parameters
        ----------
        name : str
            Property name emitted by the device.
        value :
            New value from the device.
        '''
        if self._updating or name not in self._params:
            return
        self._updating = True
        try:
            self._params[name].setValue(value)
        except Exception:
            logger.debug(f'Could not update tree for {name!r} = {value!r}')
        finally:
            self._updating = False

    @classmethod
    def example(cls) -> None:
        '''Display the tree.

        Creates a ``QApplication``, instantiates the tree, shows it,
        and runs the event loop.  Falls back to the fake device class
        from the sibling ``fake`` module if no instrument is connected.

        Intended to be called from ``__main__`` in each tree module:

        .. code-block:: python

            if __name__ == '__main__':
                QMyTree.example()
        '''
        import sys
        from qtpy.QtWidgets import QApplication
        app = QApplication.instance() or QApplication(sys.argv)
        tree = cls()
        if tree.device is None or not tree.device.isOpen():
            fake_cls = cls._fakeCls()
            if fake_cls is None:
                print(f'{cls.__name__}: instrument not found or not connected.')
                return
            print(f'{cls.__name__}: instrument not found, using {fake_cls.__name__}.')
            tree = cls(device=fake_cls())
        tree.show()
        sys.exit(app.exec())

    @classmethod
    def _fakeCls(cls) -> type | None:
        '''Return the fake instrument class from the sibling ``fake`` module.

        Looks for a ``fake.py`` in the same package as the tree class and
        returns the class named in its ``__all__``.  Returns ``None`` if no
        ``fake`` module exists.

        Works when the tree is imported normally and when its module is run
        directly as ``__main__``.
        '''
        import importlib
        import inspect
        import sys
        from pathlib import Path

        module = inspect.getmodule(cls)
        package = getattr(module, '__package__', None)

        if not package:
            tree_dir = Path(inspect.getfile(cls)).parent
            for entry in sys.path:
                if not entry:
                    continue
                try:
                    parts = tree_dir.relative_to(entry).parts
                    if parts:
                        package = '.'.join(parts)
                        break
                except ValueError:
                    continue

        if not package:
            return None
        try:
            fake_mod = importlib.import_module('.fake', package=package)
        except ImportError:
            return None
        return getattr(fake_mod, fake_mod.__all__[0])


__all__ = ['QInstrumentTree']
