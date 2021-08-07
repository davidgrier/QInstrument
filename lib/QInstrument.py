from PyQt5 import uic
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import pyqtSlot
import os
import sys


class QInstrument(QWidget):
    '''Glue class to attach a GUI created with Qt Designer
    with its hardware implementation.

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

    Methods
    -------
    properties(): list
        List of the instrument properties that are
        controlled by the QInstrument instance.

    '''

    wsetter = {'QSpinBox': 'setValue',
               'QDoubleSpinBox': 'setValue',
               'QComboBox': 'setCurrentIndex',
               'QPushButton': 'setChecked'}

    wsignal = {'QSpinBox': 'valueChanged',
               'QDoubleSpinBox': 'valueChanged',
               'QComboBox': 'currentIndexChanged',
               'QPushButton': 'toggled'}

    def __init__(self,
                 uiFile=None,
                 deviceClass=None,
                 **kwargs):
        super().__init__(**kwargs)
        self._configureUi(uiFile)
        self._configureDevice(deviceClass)

    def configureUi(self, uiFile):
        if uiFile is None:
            return
        file = sys.modules[self.__module__].__file__
        dir = os.path.dirname(os.path.abspath(file))
        uipath = os.path.join(dir, uiFile)
        form, _ = uic.loadUiType(uipath)
        self.ui = form()
        self.ui.setupUi(self)

    def configureDevice(self, deviceClass):
        if deviceClass is None:
            return
        self.device = deviceClass().find()
        if self.device is None:
            self.setEnabled(False)
        elif self.device.isOpen():
            self._updateUiValues()
            self._connectSignals()

    def properties(self):
        uiproperties = vars(self.ui).keys()
        deviceproperties = dir(self.device)
        return [p for p in uiproperties if p in deviceproperties]

    def _getMethod(self, widget, method):
        typeName = type(widget).__name__.split('.')[-1]
        return getattr(widget, method[typeName])

    def _updateUiValues(self):
        for prop in self.properties():
            widget = getattr(self.ui, prop)
            value = getattr(self.device, prop)
            update = self._getMethod(widget, self.wsetter)
            update(value)

    def _connectSignals(self):
        for prop in self.properties():
            widget = getattr(self.ui, prop)
            signal = self._getMethod(widget, self.wsignal)
            signal.connect(self._setDeviceValue)

    @pyqtSlot(bool)
    @pyqtSlot(int)
    @pyqtSlot(float)
    def _setDeviceValue(self, value):
        attr = self.sender().objectName()
        if hasattr(self.device, attr):
            setattr(self.device, attr, value)
