from PyQt5 import uic
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import pyqtSlot
import os
import sys


class QInstrument(QWidget):

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
        self.configureUi(uiFile)
        self.configureDevice(deviceClass)

    def configureUi(self, uiFile):
        if uiFile is None:
            return
        #file = __file__
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
