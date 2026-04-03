from qtpy import uic, QtWidgets, QtCore
import sys
from pathlib import Path
import logging


logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)


class QInstrumentWidget(QtWidgets.QWidget):
    '''Glue class to attach a PyQt GUI to a device interface

    A widget in the UI is linked to a pyqtProperty in the
    device interface if the widget and the property have
    the same name and the same data type.

    User interaction with a linked widget updates the corresponding
    property of the device. Programmatically changing the value of
    a linked property updates both the device and the UI.

    While QInstrumentWidget() can be used to create a hardware-enabled
    GUI directly, a better choice is to subclass QInstrumentWidget,
    providing both the name of the UI file and an object reference
    for the hardware implementation.

    ...

    Properties
    ----------
    uiFile: str
        Name of the ui file that defines the GUI. The base class
        for the widget should be QWidget.
    device: QSerialInstrument
        Hardware interface to the instrument.
    properties: list of str
        Names of device properties that are managed by the ui
    methods: list of str
        Names of device methods that are managed by the ui
    settings: dict
        Dictionary of properties and current values

    Methods
    -------
    get(pname): value
        Returns value of property with name pname
    set(pname, value):
        Set property pname to value

    Signals
    -------
    propertyChanged(pname, value)
        Emitted when a managed property changes

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

    propertyChanged = QtCore.Signal(str, object)

    def __init__(self, *args, uiFile=None, device=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.ui = self._loadUi(uiFile)
        self.device = device

    @QtCore.Property(object)
    def device(self):
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
    def properties(self):
        '''List of device properties that are controlled by the ui

           This property is configured automatically at instantiation
           and is read-only.
        '''
        return self._properties

    @QtCore.Property(list)
    def methods(self):
        '''List of device methods that are called by the ui

           This property is configured automatically at instantiation
           and is read-only.
        '''
        return self._methods

    @QtCore.Property(dict)
    def settings(self):
        '''Dictionary of properties and their current values.

        Setting this property changes values on the UI and on
        the device.'''
        return {key: self.get(key) for key in self.properties}

    @settings.setter
    def settings(self, settings):
        for key, value in settings.items():
            self.set(key, value)

    def get(self, key):
        '''Get value of named widget

        Arguments
        ---------
        key: str
            Name of property to retrieve
        '''
        if hasattr(self.ui, key):
            widget = getattr(self.ui, key)
            getter = self._wmethod(widget, self.wgetter)
            return getter()
        logger.error(f'Unknown property {key}')
        return None

    def set(self, key, value=None):
        '''Set value of named widget

        This method sets the value of the named widget
        in the UI and relies on the widget to emit a
        signal that will set the corresponding device value.

        If no value is provided, the method gets the current
        value from the device and sets the widget to that value.
        The widget's signal is blocked during this process
        to avoid a loop.

        Arguments
        ---------
        key: str
            Name of property
        value: bool | int | float | str [optional]
            Value of property
            Default: update widget value with device value
        '''
        if not hasattr(self.ui, key):
            logger.error(f'Unknown property {key}')
            return
        widget = getattr(self.ui, key)
        setter = self._wmethod(widget, self.wsetter)
        syncing = value is None
        if syncing:
            value = self.device.get(key)
            widget.blockSignals(True)
        try:
            setter(value)
        except Exception as ex:
            logger.error(f'Could not set {key} to {value}: {ex}')
        if syncing:
            widget.blockSignals(False)

    def _wmethod(self, widget, method):
        '''Return method used by widget'''
        typeName = widget.metaObject().className()
        return getattr(widget, method[typeName])

    def _loadUi(self, uiFile):
        path = Path(sys.modules[self.__module__].__file__).parent
        form, _ = uic.loadUiType(path / uiFile)
        ui = form()
        ui.setupUi(self)
        return ui

    def _identifyProperties(self):
        '''Identify properties and methods used to control device

        This method seeks out UI widgets that have the same
        name as device attributes.
        '''
        uproperties = set(vars(self.ui).keys())
        dproperties = set(self.device.properties)
        dmethods = set(self.device.methods)
        self._properties = list(uproperties & dproperties)
        self._methods = list(uproperties & dmethods)

    def _syncProperties(self):
        '''Set UI widgets to device values'''
        for prop in self.properties:
            self.set(prop)

    def _connectSignals(self):
        for prop in self.properties:
            widget = getattr(self.ui, prop)
            signal = self._wmethod(widget, self.wsignal)
            if signal is not None:
                signal.connect(self._setDeviceProperty)
        for method in self.methods:
            widget = getattr(self.ui, method)
            if isinstance(widget, QtWidgets.QPushButton):
                widget.clicked.connect(lambda m=method: self.device.execute(m))

    @QtCore.Slot(bool)
    @QtCore.Slot(int)
    @QtCore.Slot(float)
    @QtCore.Slot(str)
    def _setDeviceProperty(self, value):
        name = self.sender().objectName()
        if name in self.device.properties:
            logger.debug(f'Setting device: {name}: {value}')
            self.device.set(name, value)
            self.waitForDevice()
            self.propertyChanged.emit(name, value)

    def waitForDevice(self):
        '''Method called when setting a device property to ensure
        that the device has completed the change before allowing
        further user interaction.

        Should be overridden by subclass'''
        pass
