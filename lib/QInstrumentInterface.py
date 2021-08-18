from PyQt5 import uic
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import (pyqtSlot, pyqtProperty)
import os
import sys

import logging
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)


class QInstrumentInterface(QWidget):
    '''Glue class to attach a PyQt5 GUI to an instrument interface

    Widgets in the ui that are intended to control device
    properties must have the same name as the corresponding
    property.

    While QInstrumentInterface() can be used to create a hardware-enabled
    GUI directly, a better choice is to subclass QInstrumentInterface,
    providing both the device.ui GUI specification and the
    class for the hardware implementation.

    ...

    Inherits
    --------
    PyQt5.QtWidgets.QWidget

    Properties
    ----------
    uiFile: str
        Name of the ui file that defines the GUI. The base class
        for the widget should be QWidget.
    deviceClass: SerialInstrument
        Hardware interface to the instrument.
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

    def __init__(self, uiFile, deviceClass, **kwargs):
        super().__init__(**kwargs)
        self.ui = self._loadUi(uiFile)
        self.device = deviceClass().find()
        if self.device.isOpen():
            self._identifyProperties()
            self._syncProperties()
            self._connectSignals()
        else:
            self._properties = []
            self.setEnabled(False)

    @pyqtProperty(list)
    def properties(self):
        '''List of device properties that are controlled by the ui

           This property is configured automatically at instantiation
           and is read-only.
        '''
        return self._properties

    @pyqtProperty(dict)
    def settings(self):
        '''Dictionary of properties and their current values'''
        return {key: self.get(key) for key in self.properties}

    @settings.setter
    def settings(self, settings):
        for key, value in settings.items():
            self.set(key, value)

    def get(key):
        '''Get value of named widget

        Arguments
        ---------
        key: str
            Name of property to retrieve
        '''
        if hasattr(self.ui, key):
            widget = getattr(self.ui, key)
            getter = self._method(widget, self.wgetter)
            return getter()
        logger.error(f'Unknown property {key}')
        return None
    
    def set(key, value=None):
        '''Set value of named property

        This method explicitly sets the value of the named
        widget in the UI and relies on the widget to emit a
        signal that will set the corresponding device value.

        If no value is provided, the method set the widget
        to the value obtained from the device.

        Arguments
        ---------
        key: str
            Name of property
        value: bool | int | float | str [optional]
            Value of property
            Default: update widget value with device value

        Note
        ----
        
        '''
        if hasattr(self.ui, key):
            widget = geattr(self.ui, key)
            setter = self._method(widget, self.wsetter)
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

    
    def _method(self, widget, method):
        typeName = type(widget).__name__.split('.')[-1]
        return getattr(widget, method[typeName])

    def _loadUi(self, uiFile):
        file = sys.modules[self.__module__].__file__
        dir = os.path.dirname(os.path.abspath(file))
        uipath = os.path.join(dir, uiFile)
        form, _ = uic.loadUiType(uipath)
        ui = form()
        ui.setupUi(self)
        return ui

    def _identifyProperties(self):
        uiprops = vars(self.ui).keys()
        deviceprops = dir(self.device)
        self._properties = [p for p in uiprops if p in deviceprops]

    def _syncProperties(self):
        for prop in self.properties:
            self.set(prop)
            
    def _connectSignals(self):
        for prop in self.properties:
            widget = getattr(self.ui, prop)
            signal = self._method(widget, self.wsignal)
            if signal is not None:
                signal.connect(self._setDeviceProperty)

    @pyqtSlot(bool)
    @pyqtSlot(int)
    @pyqtSlot(float)
    @pyqtSlot(str)
    def _setDeviceProperty(self, value):
        name = self.sender().objectName()
        if hasattr(self.device, name):
            setattr(self.device, name, value)
            self.waitForDevice()
            logger.debug(f'Setting device: {name}: {value}')

    def waitForDevice(self):
        '''Can be overridden by subclass'''
        pass
