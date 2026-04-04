import logging
from .QAbstractInstrument import QAbstractInstrument

logger = logging.getLogger(__name__)


class QFakeInstrument(QAbstractInstrument):
    '''Base class for fake instruments used in UI development without hardware.

    Provides an in-memory property store and a :meth:`_register` override
    so that a concrete fake can be derived from both ``QFakeInstrument`` and
    a real instrument class with minimal boilerplate:

    .. code-block:: python

        class QFakeDS345(QFakeInstrument, QDS345):
            pass

    MRO resolution ensures that :meth:`_register` here is called instead of
    the real instrument's version, wiring every standard property to
    :attr:`_store` rather than to the serial port.  :meth:`__init__` calls
    ``QAbstractInstrument.__init__`` directly, bypassing
    ``QSerialInstrument`` so no serial port is created, then calls
    ``_registerProperties()`` and ``_registerMethods()`` if the concrete
    class provides them.

    Properties whose getters cannot be expressed through :meth:`_register`
    (non-standard response formats, internal state) must be re-registered by
    the concrete fake after calling ``super()._registerProperties()``.
    :meth:`registerProperty` overwrites any previous registration for the
    same name, so this is safe.

    Subclasses that do not inherit a real instrument class may define their
    own ``__init__``, call ``super().__init__()``, and then register
    properties directly via :meth:`registerProperty`.
    '''

    def __init__(self, *args, **kwargs) -> None:
        '''Initialise the in-memory store and register all properties.

        Calls ``QAbstractInstrument.__init__`` explicitly to bypass
        ``QSerialInstrument`` (no serial port is created), initialises
        :attr:`_store`, then calls ``_registerProperties()`` and
        ``_registerMethods()`` if the concrete class provides them.
        '''
        QAbstractInstrument.__init__(self, *args, **kwargs)
        self._store: dict = {}
        self.identification = f'Fake {type(self).__name__}'
        if hasattr(self, '_registerProperties'):
            self._registerProperties()
        if hasattr(self, '_registerMethods'):
            self._registerMethods()

    def _register(self, name: str, cmd: str, dtype: type = float) -> None:
        '''Register a property backed by :attr:`_store`.

        Overrides the real instrument's ``_register()`` via MRO.  *cmd* is
        ignored; values are stored and retrieved by *name*.

        Parameters
        ----------
        name : str
            Property name passed to :meth:`registerProperty`.
        cmd : str
            Ignored.  Present to match the real instrument's signature.
        dtype : type, optional
            Value type for storage coercion.  Default: ``float``.
        '''
        def getter():
            return self._store.get(name, dtype())
        def setter(v):
            self._store[name] = dtype(v)
        self.registerProperty(name, getter=getter, setter=setter, ptype=dtype)

    def transmit(self, data) -> None:
        '''No-op: fake instruments have no serial port.'''
        pass

    def receive(self, **kwargs) -> str:
        '''No-op: fake instruments have no serial port.'''
        return ''

    def busy(self) -> bool:
        '''Return ``False``: fake instruments are never busy.'''
        return False

    def isOpen(self) -> bool:
        '''Return ``True``: fake instruments are always available.'''
        return True


__all__ = ['QFakeInstrument']
