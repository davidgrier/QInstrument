import logging
from qtpy import QtCore
from QInstrument.lib.QAbstractInstrument import QAbstractInstrument
from QInstrument.lib.lazy import find_fake_cls

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

    To restrict the tree to a subset of properties and methods, declare
    :attr:`FIELDS` on the subclass or pass ``fields`` to ``__init__``:

    .. code-block:: python

        class QDS345Tree(QInstrumentTree):
            INSTRUMENT = QDS345
            FIELDS = ['frequency', 'amplitude', 'function']

        # or at instantiation time:
        tree = QDS345Tree(fields=['frequency', 'amplitude'])

    The order of names in :attr:`FIELDS` controls display order.  If any
    name does not match a registered property or method a warning is
    issued and all properties and methods are shown instead.

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
    FIELDS : list[str] | None
        Names of properties and/or methods to display, in display order.
        ``None`` (the default) shows all registered properties and methods.

    Parameters
    ----------
    device : QAbstractInstrument, optional
        Instrument to display.  When omitted and :attr:`INSTRUMENT` is
        set, the instrument is located via ``INSTRUMENT().find()``.
    fields : list[str] | None, optional
        Overrides :attr:`FIELDS` for this instance.  ``None`` defers to
        the class attribute.
    '''

    INSTRUMENT: type | None = None
    FIELDS: list[str] | None = None

    def __init__(self, *args,
                 device: QAbstractInstrument | None = None,
                 fields: list[str] | None = None,
                 **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._device: QAbstractInstrument | None = None
        self._params: dict[str, Parameter] = {}
        self._updating: bool = False
        self._fields: list[str] | None = (
            fields if fields is not None else self.FIELDS)
        self._visibleProps: list[str] = []
        self._visibleMethods: list[str] = []
        if device is None and self.INSTRUMENT is not None:
            device = self.INSTRUMENT().find()
        self.device = device

    @property
    def device(self) -> QAbstractInstrument | None:
        '''QAbstractInstrument: instrument bound to this tree.

        Setting this property builds the parameter tree from the
        device's registered properties and methods, syncs current
        values if the device is open, and connects signals.  Setting
        to ``None`` is a no-op.  The tree is disabled if the device
        is not open.
        '''
        return self._device

    @device.setter
    def device(self, device: QAbstractInstrument | None) -> None:
        if device is None:
            return
        self._device = device
        self._buildTree()
        if device.isOpen():
            self._connectSignals()
            self._syncProperties()
        else:
            self.setEnabled(False)

    def _resolveFields(self) -> None:
        '''Resolve :attr:`_fields` against the device registry.

        Populates :attr:`_visibleProps` and :attr:`_visibleMethods` with
        the ordered lists of property and method names to display.

        If :attr:`_fields` is ``None``, all registered properties and
        methods are used.  Otherwise each name is validated against the
        device registry.  If any name is unrecognised a warning is issued
        and the full set is used as a fallback so the instrument remains
        usable.
        '''
        all_props = self._device.properties
        all_methods = self._device.methods

        if self._fields is None:
            self._visibleProps = list(all_props)
            self._visibleMethods = list(all_methods)
            return

        known = set(all_props + all_methods)
        unknown = [n for n in self._fields if n not in known]
        if unknown:
            logger.warning(
                '%s: unrecognised field(s) %r in FIELDS/fields; '
                'displaying all properties and methods. '
                'Known names: %r',
                type(self._device).__name__,
                unknown,
                sorted(known),
            )
            self._visibleProps = list(all_props)
            self._visibleMethods = list(all_methods)
            return

        prop_set = set(all_props)
        meth_set = set(all_methods)
        self._visibleProps = [n for n in self._fields if n in prop_set]
        self._visibleMethods = [n for n in self._fields if n in meth_set]

    def _buildTree(self) -> None:
        '''Build the parameter tree from the device's registered
        properties and methods.

        Calls :meth:`_resolveFields` to determine which properties and
        methods to display, then creates typed parameters for each.
        Metadata ``minimum``/``maximum`` are mapped to parameter limits;
        ``step`` is forwarded directly.  Read-only properties are rendered
        non-editable.  Methods become ``action`` parameters (buttons).
        The root group is labelled with the instrument class name.
        '''
        self._resolveFields()
        self._params = {}
        children = []

        for name in self._visibleProps:
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

        for name in self._visibleMethods:
            children.append(dict(name=name, type='action'))

        root = Parameter.create(
            name=type(self._device).__name__,
            type='group',
            children=children,
        )
        self._params = {
            name: root.child(name)
            for name in self._visibleProps + self._visibleMethods
        }
        self.setParameters(root, showTop=True)

    def _syncProperties(self) -> None:
        '''Request current device values for all visible properties.

        Calls :meth:`device.get` for each property, which emits
        :attr:`device.propertyValue` and updates the tree via
        :meth:`_onDevicePropertyValue`.
        '''
        for name in self._visibleProps:
            self._device.get(name)

    def _connectSignals(self) -> None:
        '''Connect parameter signals to the device and device signals to the tree.

        Each writable property's ``sigValueChanged`` is wired to
        :meth:`_onParamChanged`.  Each method's ``sigActivated`` calls
        :meth:`device.execute`.  The device's ``propertyValue`` signal
        is wired to :meth:`_onDevicePropertyValue` so that external
        device changes (e.g. polling) are reflected in the tree.
        '''
        for name in self._visibleProps:
            meta = self._device.propertyMeta(name)
            if not meta.get('readonly', False):
                self._params[name].sigValueChanged.connect(
                    lambda p, v, n=name: self._onParamChanged(n, v))

        for name in self._visibleMethods:
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
                print(f'{cls.__name__}: instrument not found'
                      ' or not connected.')
                return
            print(f'{cls.__name__}: instrument not found, '
                  f'using {fake_cls.__name__}.')
            tree = cls(device=fake_cls())
        tree.show()
        sys.exit(app.exec())

    @classmethod
    def _fakeCls(cls) -> type | None:
        '''Return the fake instrument class from the sibling ``fake`` module.

        Delegates to :func:`~QInstrument.lib.lazy.find_fake_cls`.
        '''
        return find_fake_cls(cls)


__all__ = ['QInstrumentTree']
