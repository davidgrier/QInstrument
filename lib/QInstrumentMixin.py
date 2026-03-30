from pyqtgraph.Qt import QtCore
import types
from typing import Callable

_AUTO = object()  # sentinel: auto-generate getter/setter from _name convention


class QInstrumentMixin(QtCore.QObject):

    PropertyValue = bool | int | float | str
    Settings = dict[str, PropertyValue]

    def __int__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.mutex = QtCore.QMutex()
        self._properties = {}
        self._methods = {}

    def __repr__(self) -> str:
        name = self.__class__.__name__
        s = f'{name}'
        tab = (len(s) + 1) * ' '
        for k, v in self.settings.items():
            s += f'^{k}={v}$'
        s = s.replace('$^', ',\n'+tab)
        s = s.replace('^', '(')
        s = s.replace('$', ')')
        return s

    def _handshake(self, data: str, **kwargs) -> str:
        '''Transmit data to the instrument and receive its response

        Arguments
        ---------
        data: str
            String to be transmitted to the instrument
            to elicit a response

        Keywords
        --------
        Keywords are passed through to receive()

        Returns
        -------
        response: str
            Response from instrument
        '''
        self.transmit(data)
        return self.receive(**kwargs)

    def _getValue(self, query: str, dtype=float):
        '''Return value from the instrument

        Arguments
        ---------
        query: str
            String to be transmitted to the instrument
        dtype: type
            Optional specification of the data type to be returned
            Default: float

        Returns
        -------
        value: dtype
            Value returned by the instrument
        '''
        response = self.handshake(query)
        try:
            value = dtype(response)
        except ValueError:
            value = None
        return value

    def expect(self, query: str, response: str, **kwargs) -> bool:
        '''Check for expected response to a query

        Arguments
        ---------
        query: str
            String to be transmitted to the instrument
        response: str
            Expected response

        Returns
        -------
        success: bool
            True if expect response is found in the string
            returned by the instrument in response to the query
        '''
        return response in self.handshake(query, **kwargs)

    def registerProperty(self,
                         name: str,
                         getter=_AUTO,
                         setter=_AUTO,
                         ptype=float, **meta) -> None:
        '''Register a named instrument property.

        By default both getter and setter are auto-generated from the
        ``_name`` backing-attribute convention: the getter reads
        ``self._name`` and the setter writes ``ptype(value)`` back to
        ``self._name``.  Pass an explicit callable to override either,
        or pass ``setter=None`` to make the property read-only.

        Parameters
        ----------
        name : str
            Property name used with :meth:`get`, :meth:`set`, and
            attribute access.
        getter : callable, optional
            Zero-argument callable returning the current value.
            Defaults to ``lambda: getattr(self, f'_{name}')``.
        setter : callable or None, optional
            Single-argument callable applying a new value.  ``None``
            marks the property read-only.  Defaults to
            ``lambda v: setattr(self, f'_{name}', ptype(v))``.
        ptype : type
            Python type of the property value (``int``, ``float``,
            ``bool``, ``str``).  Drives the default setter coercion and
            is stored for use by UI generators such as ``QCameraTree``.
        **meta :
            Additional metadata (e.g. ``minimum``, ``maximum``, ``step``).
        '''
        if getter is _AUTO:
            def getter(): return getattr(self, f'_{name}')
        if setter is _AUTO:
            def setter(v): return setattr(self, f'_{name}', ptype(v))
        self._properties[name] = dict(
            getter=getter, setter=setter, ptype=ptype, **meta)

    @property
    def properties(self) -> list[str]:
        '''List of instrument properties'''
        return list(self._properties.keys())

    @property
    def settings(self) -> Settings:
        '''Dictionary of instrument settings'''
        return {p: self._properties[p]['getter']()
                for p in self.properties}

    @settings.setter
    def settings(self, settings: Settings) -> None:
        for key, value in settings.items():
            if key in self._properties:
                setter = self._properties[key]['setter']
                if setter is not None:
                    setter(value)

    @QtCore.pyqtSlot(str, object)
    def set(self, key: str, value: PropertyValue) -> None:
        '''Set a registered property to the given value.

        Parameters
        ----------
        key : str
            Property name.
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
            else:
                logger.debug(f'Setting {key}: {value}')
                setter(value)

    @QtCore.pyqtSlot(str)
    def get(self, key: str) -> PropertyValue | None:
        '''Return the current value of a registered property.

        Emits :attr:`propertyValue` with the name and value.

        Parameters
        ----------
        key : str
            Property name.

        Returns
        -------
        PropertyValue or None
            Current value, or ``None`` if the property is unknown.
        '''
        with QtCore.QMutexLocker(self.mutex):
            if key in self._properties:
                value = self._properties[key]['getter']()
            else:
                logger.error(f'Unknown property: {key}')
                return None
        self.propertyValue.emit(key, value)
        return value

    def registerMethod(self, name: str, method: Callable) -> None:
        '''Register a named callable method.

        Parameters
        ----------
        name : str
            Method name used with :meth:`execute`.
        method : callable
            Zero-argument callable to invoke.
        '''
        self._methods[name] = method

    @property
    def methods(self) -> list[str]:
        '''List of instrument methods'''
        kv = vars(type(self)).items()
        return [k for k, v in kv if isinstance(v, types.FunctionType)]

    @QtCore.pyqtSlot(str)
    def execute(self, key: str) -> None:
        '''Call a registered method by name.

        Parameters
        ----------
        key : str
            Method name.
        '''
        with QtCore.QMutexLocker(self.mutex):
            if key in self._methods:
                self._methods[key]()
            else:
                logger.error(f'Unknown method: {key}')
