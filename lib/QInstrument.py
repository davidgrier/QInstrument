from PyQt5 import uic
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import (pyqtSlot, pyqtProperty)
import os
import sys

import logging
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)


class QInstrument(QWidget):
    '''Glue class to attach a PyQt5 GUI to an instrument interface

    Widgets in the ui that are intended to control device
    properties must have the same name as the corresponding
    property.

    While QInstrument() can be used to create a hardware-enabled
    GUI directly, a better choice is to subclass QInstrument,
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

    wsignal = {'QCheckBox':      'toggled',
               'QComboBox':      'currentIndexChanged',
               'QDoubleSpinBox': 'valueChanged',
               'QGroupBox':      'toggled',
               'QLineEdit':      'editingFinished',
               'QPushButton':    'toggled',
               'QRadioButton':   'toggled',
               'QSpinBox':       'valueChanged'}

    def __init__(self, uiFile, deviceClass,
                 **kwargs):
        super().__init__(**kwargs)
        self._configureUi(uiFile)
        self._configureDevice(deviceClass)
        self._configureProperties()

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

    def set(key, value):
        '''Set value of named property

        Arguments
        ---------
        key: str
            Name of property
        value: (bool, int, float, str)
            Value of property

        Note
        ----
        This method explicitly sets the value of the named
        widget in the UI and relies on the widget to set the
        corresponding device value.
        '''
        if hasattr(self.ui, key):
            setattr(self.ui, key, value)

    def get(key):
        '''Get value of named property

        Arguments
        ---------
        key: str
            Name of property to retrieve
        '''
        getattr(self.ui, key, None)

    def waitForDevice(self):
        '''Can be overridden by subclass'''
        pass
            
    def _configureUi(self, uiFile):
        file = sys.modules[self.__module__].__file__
        dir = os.path.dirname(os.path.abspath(file))
        uipath = os.path.join(dir, uiFile)
        form, _ = uic.loadUiType(uipath)
        self.ui = form()
        self.ui.setupUi(self)

    def _configureDevice(self, deviceClass):
        self.device = deviceClass().find()
        if self.device is None:
            self.setEnabled(False)
        elif self.device.isOpen():
            self._updateUiValues()
            self._connectSignals()

    def _configureProperties(self):
        uiprops = vars(self.ui).keys()
        deviceprops = dir(self.device)
        self._properties = [p for p in uiprops if p in deviceprops]
        
    def _method(self, widget, method):
        typeName = type(widget).__name__.split('.')[-1]
        return getattr(widget, method[typeName])

    def _updateUiValues(self):
        for prop in self.properties():
            widget = getattr(self.ui, prop)
            value = getattr(self.device, prop)
            update = self._method(widget, self.wsetter)
            update(value)

    def _connectSignals(self):
        for prop in self.properties():
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
            setattr(self.device, attr, value)
            self.waitForDevice()
            logger.debug(f'Setting device: {name}: {value}')
