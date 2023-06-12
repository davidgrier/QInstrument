from PyQt5 import uic
from PyQt5.QtWidgets import (QWidget, QPushButton)
from PyQt5.QtCore import (pyqtProperty, pyqtSlot, pyqtSignal)
import sys
from pathlib import Path
import logging


logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)


class QInstrumentWidget(QWidget):
    '''Glue class to attach a PyQt5 GUI to a device interface

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

    Inherits
    --------
    PyQt5.QtWidgets.QWidget

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

    propertyChanged = pyqtSignal(str, object)

    def __init__(self, *args, uiFile=None, device=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.ui = self._loadUi(uiFile)
        self.device = device

    @pyqtProperty(object)
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

    @pyqtProperty(list)
    def properties(self):
        '''List of device properties that are controlled by the ui

           This property is configured automatically at instantiation
           and is read-only.
        '''
        return self._properties

    @pyqtProperty(list)
    def methods(self):
        '''List of device methods that are called by the ui

           This property is configured automatically at instantiation
           and is read-only.
        '''
        return self._methods

    @pyqtProperty(dict)
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
        if hasattr(self.ui, key):
            widget = getattr(self.ui, key)
            setter = self._wmethod(widget, self.wsetter)
            if value is None:
                value = getattr(self.device, key, None)
                self.blockSignals(True)
            try:
                setter(value)
            except Exception as ex:
                logger.error(f'Could not set {key} to {value}: {ex}')
            self.blockSignals(False)
        else:
            logger.error(f'Unknown property {key}')

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
            if isinstance(widget, QPushButton):
                widget.clicked.connect(getattr(self.device, method))

    @pyqtSlot(bool)
    @pyqtSlot(int)
    @pyqtSlot(float)
    @pyqtSlot(str)
    def _setDeviceProperty(self, value):
        name = self.sender().objectName()
        if hasattr(self.device, name):
            logger.debug(f'Setting device: {name}: {value}')
            setattr(self.device, name, value)
            self.waitForDevice()
            self.propertyChanged.emit(name, value)

    def waitForDevice(self):
        '''Method called when setting a device property to ensure
        that the device has completed the change before allowing
        further user interaction.

        Should be overridden by subclass'''
        pass
