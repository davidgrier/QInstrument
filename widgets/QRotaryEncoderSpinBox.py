from PyQt5 import uic
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import pyqtSlot
import os
from matplotlib.colors import (to_rgb, to_hex)
import numpy as np


class QRotaryEncoderSpinBox(QWidget):
    '''QDoubleSpinBox controlled by a rotary encoder widget

    ...

    Inherits
    --------
    PyQt5.QtWidgets.QWidget

    Properties
    ----------
    colors: tuple or list [optional]
        The SpinBox background color advances from
        color[0] to color[1] as the value() increases
        from minimum() to maximum()

    QRotaryEncoderSpinBox inherits properties from QDoubleSpinBox:

    decimals
    maximum
    minimum
    range
    prefix
    suffix
    singleStep
    stepType
    value

    These properties are accessed through inherited methods:

    Methods
    -------
    decimals(): int
    setDecimals(number: int)

    maximum(): float
    setMaximum(value: float)

    minimum(): float
    setMinimum(value: float)

    setRange(minimum: float, maximum: float)

    prefix(): str
    setPrefix(value: str)

    suffix(): str
    setSuffix(value: str)

    singleStep(): float
    setSingleStep(value: float)

    stepType(): enum
    setStepType(value: enum)

    value(): float
    setValue(value: float)

    Signals
    -------
    valueChanged(float)

    '''

    def __init__(self, *args, colors=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.ui = self._loadUi()
        self._inheritMethods()
        self.setColors(colors or ('white', 'red'))

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

    def colors(self):
        return self._colors

    def setColors(self, colors):
        self._colors = colors
        if colors is None:
            self.valueChanged.disconnect(self._updateAppearance)
        else:
            self._c1 = np.array(to_rgb(colors[0]))
            self._c2 = np.array(to_rgb(colors[1]))
            self.valueChanged.connect(self._updateAppearance)

    def _setBackgroundColor(self, color):
        style = (f'QDoubleSpinBox {{'
                 f' background-color: {color};'
                 f' selection-background-color: {color}; }}')
        self.ui.value.setStyleSheet(style)

    @pyqtSlot(float)
    def _updateAppearance(self, value):
        f = (value - self.minimum())/(self.maximum() - self.minimum())
        color = to_hex((1-f)*self._c1 + f*self._c2)
        self._setBackgroundColor(color)


def example():
    from PyQt5.QtWidgets import QApplication

    app = QApplication([])
    widget = QRotaryEncoderSpinBox()
    widget.setRange(0., 5)
    widget.setSingleStep(0.01)
    widget.setValue(0)
    widget.setSuffix(' W')
    widget.setColors(('white', '#68ff00'))
    widget.show()
    app.exec()


if __name__ == '__main__':
    example()
