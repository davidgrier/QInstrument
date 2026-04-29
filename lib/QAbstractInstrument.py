import logging
from qtpy import QtCore
from typing import Callable


logger = logging.getLogger(__name__)

_AUTO = object()  # sentinel: auto-generate getter/setter from _name convention


class QAbstractInstrument(QtCore.QObject):
    '''Abstract base class for scientific instruments.

    Models instrument state as named properties registered via
    :meth:`registerProperty` and accessed through the thread-safe
    :meth:`get` and :meth:`set` slots.  Methods are registered via
    :meth:`registerMethod` and invoked by name via :meth:`execute`.

    This class has no concept of hardware communication.  A concrete
    transport subclass (e.g. :class:`QSerialInstrument`) provides the
    I/O layer and higher-level communication helpers.

    Signals
    -------
    propertyValue(str, object)
        Emitted by :meth:`get` and :meth:`set` with the property name
        and its current value.
    '''

    PropertyValue = bool | int | float | str
    Settings = dict[str, PropertyValue]

    propertyValue = QtCore.Signal(str, object)

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.mutex = QtCore.QMutex()
        self._properties = {}
        self._methods = {}
        self._registerProperties()
        self._registerMethods()

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}()'

    def _registerProperties(self) -> None:
        '''Register instrument properties.

        Called automatically by :meth:`__init__`.  No-op base
        implementation; concrete instruments override this to call
        :meth:`registerProperty` for each of their properties.
        Subclasses that extend the property set of a parent instrument
        should call ``super()._registerProperties()`` first.
        '''

    def _registerMethods(self) -> None:
        '''Register instrument methods.

        Called automatically by :meth:`__init__`.  No-op base
        implementation; concrete instruments override this to call
        :meth:`registerMethod` for each of their methods.
        Subclasses that extend the method set of a parent instrument
        should call ``super()._registerMethods()`` first.
        '''

    def registerProperty(self,
                         name: str,
                         getter: Callable | None = _AUTO,
                         setter: Callable | None = _AUTO,
                         ptype: type = float, **meta) -> None:
        '''Register a named instrument property.

        By default both getter and setter are auto-generated from the
        ``_name`` backing-attribute convention: the getter reads
        ``self._name`` and the setter writes ``ptype(value)`` back to
        ``self._name``.  Pass an explicit callable to override either,
        or pass ``setter=None`` to make the property read-only.

        Parameters
        ----------
        name : str
            Property name used with :meth:`get` and :meth:`set`.
        getter : callable, optional
            Zero-argument callable returning the current value.
            Default: ``lambda: getattr(self, f'_{name}')``.
        setter : callable or None, optional
            Single-argument callable that applies a new value.
            ``None`` marks the property read-only.
            Default: ``lambda v: setattr(self, f'_{name}', ptype(v))``.
        ptype : type, optional
            Python type of the property value (``int``, ``float``,
            ``bool``, or ``str``).  Used for default setter coercion
            and stored as metadata for UI generators.
            Default: ``float``.
        **meta :
            Arbitrary metadata stored alongside the property
            (e.g. ``minimum``, ``maximum``, ``step``).
        '''
        if getter is _AUTO:
            def _getter(): return getattr(self, f'_{name}')
            getter = _getter
        if setter is _AUTO:
            def _setter(v): return setattr(self, f'_{name}', ptype(v))
            setter = _setter
        self._properties[name] = dict(
            getter=getter, setter=setter, ptype=ptype, **meta)

    def registerMethod(self,
                       name: str,
                       method: Callable[[], None]) -> None:
        '''Register a named zero-argument callable.

        Registered methods can be invoked by name via :meth:`execute`.

        Parameters
        ----------
        name : str
            Method name used with :meth:`execute`.
        method : callable
            Zero-argument callable to invoke.
        '''
        self._methods[name] = method

    @property
    def properties(self) -> list[str]:
        '''Names of all registered instrument properties.'''
        return list(self._properties.keys())

    @property
    def settings(self) -> Settings:
        '''Current values of all writable registered properties.

        Getting this property calls every qualifying getter, which may
        issue instrument queries.  A property qualifies when its setter
        is not ``None`` (writable).

        Setting it calls each registered setter for keys present in the
        supplied dict, skipping unknown keys and read-only properties.
        Unlike :meth:`set`, the setter does not emit
        :attr:`propertyValue` for each key; call
        :meth:`_syncProperties` after a bulk restore if the UI must
        reflect the new values.

        Subclasses that need to exclude specific properties from
        save/restore (e.g. motion-speed parameters that must not be
        silently overwritten on reconnect) should override both the
        getter and setter to filter those names.  See
        :class:`QProscan` for an example.
        '''
        with QtCore.QMutexLocker(self.mutex):
            props = list(self._properties.items())
        return {
            name: info['getter']()
            for name, info in props
            if info['setter'] is not None
        }

    @settings.setter
    def settings(self, settings: Settings) -> None:
        with QtCore.QMutexLocker(self.mutex):
            calls = [(self._properties[k]['setter'], v)
                     for k, v in settings.items()
                     if k in self._properties]
        for setter, value in calls:
            if setter is not None:
                setter(value)

    @property
    def methods(self) -> list[str]:
        '''Names of all registered instrument methods.'''
        return list(self._methods.keys())

    @QtCore.Slot(str)
    def get(self, key: str) -> PropertyValue | None:
        '''Return the current value of a registered property.

        Thread-safe Qt slot.  The registry lock is released before
        calling the getter, so the getter may safely call other
        instrument methods without deadlocking.  Emits
        :attr:`propertyValue` with the name and value.  Logs an error
        and returns ``None`` if the key is not registered.

        Parameters
        ----------
        key : str
            Registered property name.

        Returns
        -------
        PropertyValue or None
            Current value, or ``None`` if *key* is unknown.
        '''
        with QtCore.QMutexLocker(self.mutex):
            if key not in self._properties:
                logger.error(f'Unknown property: {key}')
                return None
            getter = self._properties[key]['getter']
        value = getter()
        self.propertyValue.emit(key, value)
        return value

    @QtCore.Slot(str, object)
    def set(self, key: str, value: PropertyValue) -> None:
        '''Set a registered property to the given value.

        Thread-safe Qt slot.  The registry lock is released before
        calling the setter, so the setter may safely call other
        instrument methods without deadlocking.  Emits
        :attr:`propertyValue` with the new value on success.  Logs a
        warning if the property is read-only and an error if the key
        is not registered.

        Parameters
        ----------
        key : str
            Registered property name.
        value : PropertyValue
            New value to assign.
        '''
        with QtCore.QMutexLocker(self.mutex):
            if key not in self._properties:
                logger.error(f'Unknown property: {key}')
                return
            setter = self._properties[key]['setter']
        if setter is None:
            logger.warning(f'Property {key!r} is read-only')
            return
        logger.debug(f'Setting {key}: {value}')
        setter(value)
        self.propertyValue.emit(key, value)

    def propertyMeta(self, name: str) -> dict:
        '''Return a copy of the metadata for a registered property.

        Returns an empty dict if *name* is not registered.
        Excludes the internal getter and setter callables.

        Parameters
        ----------
        name : str
            Registered property name.

        Returns
        -------
        dict
            Metadata dict (e.g. ``ptype``, ``minimum``, ``maximum``,
            ``step``, ``debounce``).
        '''
        with QtCore.QMutexLocker(self.mutex):
            if name not in self._properties:
                return {}
            info = self._properties[name].copy()
        info.pop('getter', None)
        info['readonly'] = info.pop('setter', None) is None
        return info

    @QtCore.Slot(str)
    def execute(self, key: str) -> None:
        '''Call a registered method by name.

        Thread-safe Qt slot.  Logs an error if the key is not
        registered.

        Parameters
        ----------
        key : str
            Registered method name.
        '''
        with QtCore.QMutexLocker(self.mutex):
            if key not in self._methods:
                logger.error(f'Unknown method: {key}')
                return
            method = self._methods[key]
        method()


__all__ = ['QAbstractInstrument']
