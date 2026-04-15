import math
from pathlib import Path
import inspect
import logging

from qtpy import uic, QtWidgets, QtCore

from .Configure import Configure
from .QReconcileDialog import QReconcileDialog


logger = logging.getLogger(__name__)


def _values_differ(a: object, b: object) -> bool:
    '''Return True if *a* and *b* represent meaningfully different values.

    Floats are compared with a relative tolerance of 1e-6 and an
    absolute tolerance of 1e-9 to avoid spurious mismatches from
    JSON round-tripping.  All other types use exact equality.
    '''
    if isinstance(a, float) and isinstance(b, float):
        return not math.isclose(a, b, rel_tol=1e-6, abs_tol=1e-9)
    return a != b


class QInstrumentWidget(QtWidgets.QWidget):
    '''Widget that auto-binds a Qt Designer UI to a QAbstractInstrument.

    A named widget in the UI is linked to a registered device property
    when their names match and the widget type appears in :attr:`wsetter`,
    :attr:`wgetter`, and :attr:`wsignal`.  User interaction with a linked
    widget calls :meth:`device.set`; the device value is read back and
    the widget is updated without re-triggering the signal.

    Subclass this, declare :attr:`UIFILE`, and supply a device:

    .. code-block:: python

        class QDS345Widget(QInstrumentWidget):
            UIFILE = 'DS345.ui'

            def __init__(self, *args, **kwargs):
                super().__init__(*args, device=QDS345(), **kwargs)

    The ``.ui`` file is resolved relative to the subclass's source
    directory, so it works regardless of the working directory.

    Class Attributes
    ----------------
    UIFILE : str | None
        Filename of the Qt Designer ``.ui`` file.  Must be set by each
        subclass.
    INSTRUMENT : type | None
        Concrete instrument class to instantiate and search for when no
        ``device`` is supplied to ``__init__``.  When set, the base class
        calls ``INSTRUMENT().find()`` automatically so subclasses need not
        override ``__init__`` solely to locate the device.
    wsetter : dict[str, str]
        Maps widget class name to its value-setter method name.
    wgetter : dict[str, str]
        Maps widget class name to its value-getter method name.
    wsignal : dict[str, str]
        Maps widget class name to the signal emitted on user interaction.

    Signals
    -------
    propertyChanged(str, object)
        Emitted after a linked widget updates the device, carrying
        the property name and the new value.
    '''

    wsetter = {'QCheckBox':      'setChecked',
               'QComboBox':      'setCurrentIndex',
               'QDoubleSpinBox': 'setValue',
               'QGroupBox':      'setChecked',
               'QLabel':         'setText',
               'QLineEdit':      'setText',
               'QPushButton':    'setChecked',
               'QRadioButton':   'setChecked',
               'QSpinBox':       'setValue'}

    wgetter = {'QCheckBox':      'isChecked',
               'QComboBox':      'currentIndex',
               'QDoubleSpinBox': 'value',
               'QGroupBox':      'isChecked',
               'QLabel':         'text',
               'QLineEdit':      'text',
               'QPushButton':    'isChecked',
               'QRadioButton':   'isChecked',
               'QSpinBox':       'value'}

    wsignal = {'QCheckBox':      'toggled',
               'QComboBox':      'currentIndexChanged',
               'QDoubleSpinBox': 'valueChanged',
               'QGroupBox':      'toggled',
               'QLineEdit':      'editingFinished',
               'QPushButton':    'toggled',
               'QRadioButton':   'toggled',
               'QSpinBox':       'valueChanged'}

    UIFILE: str | None = None
    INSTRUMENT: type | None = None
    HARDWARE_DOMINANT: bool = False

    propertyChanged = QtCore.Signal(str, object)
    closeRequested = QtCore.Signal()

    def __init__(self, *args, device=None, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._device = None
        self._configure = Configure()
        self._restored = False
        uic.loadUi(self._uiPath(), self)
        if device is None and self.INSTRUMENT is not None:
            device = self.INSTRUMENT().find()
        self.device = device

    @QtCore.Property(object)
    def device(self):
        '''QAbstractInstrument: instrument bound to this widget.

        Setting this property identifies matching properties and methods,
        syncs the UI to current device values (if open), and connects
        widget signals to the device.  Setting to ``None`` is a no-op.
        The widget is disabled if the device is not open.
        '''
        return self._device

    @device.setter
    def device(self, device):
        if device is None:
            return
        self._device = device
        self._identifyProperties()
        if self._device.isOpen():
            self._syncProperties()
            self._connectSignals()
        else:
            self.setEnabled(False)

    @QtCore.Property(list)
    def properties(self) -> list[str]:
        '''list[str]: device property names managed by this widget.'''
        return self._properties

    @QtCore.Property(list)
    def methods(self) -> list[str]:
        '''list[str]: device method names managed by this widget.'''
        return self._methods

    @QtCore.Property(dict)
    def settings(self) -> dict:
        '''dict: current values of all managed properties.

        Getting reads each linked widget.  Setting calls :meth:`set`
        for each key present in the supplied dict.
        '''
        return {key: self.get(key) for key in self.properties}

    @settings.setter
    def settings(self, settings):
        for key, value in settings.items():
            self.set(key, value)

    def get(self, key: str):
        '''Return the current value of a named widget.

        Parameters
        ----------
        key : str
            Name of the property whose widget value to read.

        Returns
        -------
        object or None
            Current widget value, or ``None`` if *key* is not found.
        '''
        widget = self.__dict__.get(key)
        if isinstance(widget, QtWidgets.QWidget):
            getter = self._wmethod(widget, self.wgetter)
            if getter is None:
                return None
            return getter()
        logger.error(f'Unknown property {key}')
        return None

    def set(self, key: str, value=None) -> None:
        '''Set the value of a named widget.

        When *value* is provided, sets the widget directly; the widget
        then emits its signal, which propagates the change to the device.
        When *value* is ``None``, reads the current value from the device
        and updates the widget with signals blocked to avoid a feedback
        loop.

        Parameters
        ----------
        key : str
            Name of the property to set.
        value : bool | int | float | str | None, optional
            Value to apply.  ``None`` (default) syncs the widget from
            the device.
        '''
        widget = self.__dict__.get(key)
        if not isinstance(widget, QtWidgets.QWidget):
            logger.error(f'Unknown property {key}')
            return
        setter = self._wmethod(widget, self.wsetter)
        if setter is None:
            logger.debug(f'No setter for widget type of {key!r}; skipping')
            return
        syncing = value is None
        if syncing:
            value = self.device.get(key)
        try:
            if syncing:
                with QtCore.QSignalBlocker(widget):
                    setter(value)
            else:
                setter(value)
        except Exception as ex:
            logger.error(f'Could not set {key} to {value}: {ex}')

    def _wmethod(self,
                 widget: QtWidgets.QWidget,
                 method: dict) -> 'callable | None':
        '''Return the bound method named by *method* for *widget*'s type.

        Returns ``None`` if the widget's class is not in *method*, so
        callers can skip unknown widget types without raising.

        Parameters
        ----------
        widget : QWidget
            The target widget.
        method : dict
            One of :attr:`wsetter`, :attr:`wgetter`, or :attr:`wsignal`,
            mapping widget class name to method name.
        '''
        typeName = widget.metaObject().className()
        name = method.get(typeName)
        if name is None:
            return None
        return getattr(widget, name)

    @classmethod
    def _uiPath(cls) -> Path:
        '''Return the absolute path to this class's UI file.

        Resolves :attr:`UIFILE` relative to the directory of the class
        in the MRO that defines it, so subclasses that inherit
        :attr:`UIFILE` without overriding it resolve correctly.
        '''
        for klass in cls.__mro__:
            if 'UIFILE' in klass.__dict__:
                return Path(inspect.getfile(klass)).parent / klass.UIFILE
        raise AttributeError(f'{cls.__name__} has no UIFILE defined')

    def _identifyProperties(self) -> None:
        '''Populate :attr:`_properties` and :attr:`_methods`.

        Intersects the set of UI widget names with the device's
        registered property and method names.
        '''
        uwidgets = {name for name, obj in self.__dict__.items()
                    if isinstance(obj, QtWidgets.QWidget)}
        dproperties = set(self.device.properties)
        dmethods = set(self.device.methods)
        self._properties = list(uwidgets & dproperties)
        self._methods = list(uwidgets & dmethods)

    def _syncProperties(self) -> None:
        '''Set all linked widgets to current device values.'''
        for prop in self.properties:
            self.set(prop)

    def _connectSignals(self) -> None:
        '''Connect linked widget signals to the device and propertyChanged.

        Properties with a ``debounce`` metadata value are connected
        through a single-shot :class:`QTimer` so that rapid widget
        changes (e.g. spinbox scrolling) are coalesced: only the final
        value after the debounce interval elapses is sent to the device.
        '''
        for prop in self.properties:
            widget = getattr(self, prop)
            signal = self._wmethod(widget, self.wsignal)
            if signal is None:
                continue
            debounce_ms = self.device.propertyMeta(prop).get('debounce', 0)
            if debounce_ms:
                self._connectDebounced(prop, signal, debounce_ms)
            else:
                signal.connect(self._setDeviceProperty)
        for method in self.methods:
            widget = getattr(self, method)
            if isinstance(widget, QtWidgets.QPushButton):
                widget.clicked.connect(
                    lambda m=method: self.device.execute(m))

    def _connectDebounced(
            self,
            prop: str,
            signal: QtCore.Signal,
            debounce_ms: int
    ) -> None:
        '''Connect *signal* to :meth:`_applyProperty` via a debounce timer.

        Each call creates a single-shot :class:`QTimer`.  Every signal
        emission stores the latest value and restarts the timer; the
        device is only updated when the timer fires (i.e. when the user
        pauses for *debounce_ms* milliseconds).

        Parameters
        ----------
        prop : str
            Property name passed to :meth:`_applyProperty`.
        signal : QtCore.Signal
            The widget signal to debounce.
        debounce_ms : int
            Quiet period in milliseconds before the device is updated.
        '''
        timer = QtCore.QTimer(self)
        timer.setSingleShot(True)
        timer.setInterval(debounce_ms)
        pending = [None]

        def on_change(value):
            pending[0] = value
            timer.start()

        def on_timeout():
            self._applyProperty(prop, pending[0])

        signal.connect(on_change)
        timer.timeout.connect(on_timeout)

    def _applyProperty(
            self, name: str, value: bool | int | float | str
    ) -> None:
        '''Send *value* to the device for property *name*.

        Called by both :meth:`_setDeviceProperty` (direct path) and the
        debounce timer timeout (rate-limited path).

        Parameters
        ----------
        name : str
            Registered property name.
        value : bool | int | float | str
            New value to send to the device.
        '''
        if name in self.device.properties:
            logger.debug(f'Setting device: {name}: {value}')
            self.device.set(name, value)
            self.waitForDevice()
            self.propertyChanged.emit(name, value)

    @QtCore.Slot(bool)
    @QtCore.Slot(int)
    @QtCore.Slot(float)
    @QtCore.Slot(str)
    def _setDeviceProperty(self, value: bool | int | float | str) -> None:
        '''Slot connected to non-debounced widget signals.

        Reads the sender's object name and delegates to
        :meth:`_applyProperty`.
        '''
        self._applyProperty(self.sender().objectName(), value)

    def waitForDevice(self) -> None:
        '''Block until the device has completed the most recent change.

        Called by :meth:`_setDeviceProperty` after every device write.
        The base implementation is a no-op; subclasses should override
        this if the instrument requires a settling delay or a busy-poll.
        '''
        pass

    def showEvent(self, event) -> None:
        '''Reconcile device settings on first show.

        On the first time the widget is shown, calls
        :meth:`_restoreSettings` to reconcile hardware state with any
        saved configuration, then re-syncs the UI.  Subsequent show
        events are passed through without reconciling.
        '''
        if not self._restored and self._device is not None and self._device.isOpen():
            self._restoreSettings()
            self._syncProperties()
            self._restored = True
        super().showEvent(event)

    def _restoreSettings(self) -> None:
        '''Reconcile hardware state with the saved configuration file.

        Reads the current hardware state via :attr:`device.settings`
        and the saved configuration via :meth:`Configure.read`.

        - **No saved file**: writes hardware values to the config file
          and returns without changing the hardware.
        - **Files match**: no action.
        - **Files differ**: shows a :class:`QReconcileDialog`.  If the
          user chooses "Keep Hardware" (or dismisses the dialog), the
          config file is updated to reflect the hardware.  If the user
          chooses "Use Saved", the saved values are pushed to the device.

        The default button in the dialog is controlled by
        :attr:`HARDWARE_DOMINANT`.
        '''
        hw = self._device.settings
        saved = self._configure.read(self._device)

        if saved is None:
            self._configure.save(self._device)
            return

        diff_keys = [
            k for k in hw
            if k in saved and _values_differ(hw[k], saved[k])
        ]

        if not diff_keys:
            return

        dialog = QReconcileDialog(
            hw, saved, diff_keys,
            hardware_dominant=self.HARDWARE_DOMINANT,
            parent=self,
        )
        accepted = dialog.exec()

        if not accepted or dialog.keep_hardware:
            self._configure.save(self._device)
        else:
            self._device.settings = saved

    def closeEvent(self, event) -> None:
        '''Save device settings when the widget is closed.

        Calls :meth:`Configure.save` to persist the current device state
        to ``~/.QInstrument/<ClassName>.json`` before passing the event
        to the parent class.  Only saves if the widget was previously
        shown, so that test widgets closed during teardown do not
        overwrite saved configuration.
        '''
        if self._restored and self._device is not None:
            self._configure.save(self._device)
        super().closeEvent(event)

    @classmethod
    def example(cls) -> None:
        '''Display the widget.

        Creates a ``QApplication``, instantiates the widget, shows it,
        and runs the event loop.

        Intended to be called from ``__main__`` in each widget module:

        .. code-block:: python

            if __name__ == '__main__':
                QMyWidget.example()
        '''
        import sys
        import inspect
        import importlib
        from qtpy.QtWidgets import QApplication
        app = QApplication.instance() or QApplication(sys.argv)
        widget = cls()
        if widget.device is None or not widget.device.isOpen():
            fake_cls = cls._fakeCls()
            if fake_cls is None:
                print(f'{cls.__name__}: instrument not found or not connected.')
                return
            print(f'{cls.__name__}: instrument not found, using {fake_cls.__name__}.')
            widget = cls(device=fake_cls())
        widget.adjustSize()
        widget.show()
        sys.exit(app.exec())

    @classmethod
    def _fakeCls(cls) -> type | None:
        '''Return the fake instrument class from the sibling ``fake`` module.

        Looks for a ``fake.py`` in the same package as the widget class and
        returns the class named in its ``__all__``.  Returns ``None`` if no
        ``fake`` module exists.

        Works when the widget is imported normally and when its module is run
        directly as ``__main__`` (e.g. ``python3 widget.py``), in which case
        the package is derived from the file path and :data:`sys.path`.
        '''
        import importlib
        import inspect
        import sys
        from pathlib import Path

        module = inspect.getmodule(cls)
        package = getattr(module, '__package__', None)

        if not package:
            widget_dir = Path(inspect.getfile(cls)).parent
            for entry in sys.path:
                if not entry:
                    continue
                try:
                    parts = widget_dir.relative_to(entry).parts
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

__all__ = ['QInstrumentWidget']
