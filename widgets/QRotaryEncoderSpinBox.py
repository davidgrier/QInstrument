from PyQt5 import uic
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import (pyqtSlot, pyqtProperty)
import os
from matplotlib.colors import (to_rgb, to_hex)
import numpy as np


class QRotaryEncoderSpinBox(QWidget):

    def __init__(self, *args,
                 minColor=None,
                 maxColor=None,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self.minColor = minColor or 'white'
        self.maxColor = maxColor or '#65ff00'
        self.ui = self._loadUi()
        self._inheritMethods()
        self.valueChanged.connect(self.updateAppearance)

    def _loadUi(self):
        uifile = os.path.splitext(__file__)[0] + '.ui'
        dir = os.path.dirname(os.path.abspath(__file__))
        uipath = os.path.join(dir, uifile)
        form, _ = uic.loadUiType(uipath)
        ui = form()
        ui.setupUi(self)
        return ui

    def _inheritMethods(self):
        methods = ['decimals', 'setDecimals',
                   'maximum', 'setMaximum',
                   'minimum', 'setMinimum',
                   'setRange',
                   'prefix', 'setPrefix',
                   'suffix', 'setSuffix',
                   'singleStep', 'setSingleStep',
                   'stepType', 'setStepType',
                   'value', 'setValue', 'valueChanged']
        for method in methods:
            setattr(self, method, getattr(self.ui.value, method))

    @pyqtProperty(object)
    def minColor(self):
        return self._minColor

    @minColor.setter
    def minColor(self, value):
        self._minColor = value
        self._c1 = np.array(to_rgb(value))

    @pyqtProperty(object)
    def maxColor(self):
        return self._maxColor

    @maxColor.setter
    def maxColor(self, value):
        self._maxColor = value
        self._c2 = np.array(to_rgb(value))

    def setBackgroundColor(self, color):
        style = f'QDoubleSpinBox {{background-color: {color}; }}'
        self.ui.value.setStyleSheet(style)

    @pyqtSlot(float)
    def updateAppearance(self, value):
        f = (value - self.minimum())/(self.maximum() - self.minimum())
        color = to_hex((1-f)*self._c1 + f*self._c2)
        self.setBackgroundColor(color)


def main():
    from PyQt5.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    widget = QRotaryEncoderSpinBox()
    widget.setRange(0., 5)
    widget.setSingleStep(0.01)
    widget.setValue(0)
    widget.setSuffix(' W')
    widget.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
