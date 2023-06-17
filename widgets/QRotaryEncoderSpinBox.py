from PyQt5 import uic
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import (QObject, QEvent, pyqtSlot)
from PyQt5.Qt import Qt
from matplotlib.colors import (to_rgb, to_hex)
import numpy as np
from pathlib import Path


class SuppressArrowKeys(QObject):

    def __init__(self, parent):
        super().__init__(parent)

    def eventFilter(self, object, event):
        if event.type() == QEvent.KeyPress:
            if event.key() in [Qt.Key_Up, Qt.Key_Down]:
                return True
        return False


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
        self.filter = SuppressArrowKeys(self)
        self.ui.value.installEventFilter(self.filter)
        self._inheritMethods()
        self.setColors(colors or ('white', 'red'))

    def _loadUi(self):
        uipath = Path(__file__).with_suffix('.ui')
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
            self.valueChanged.disconnect(self._setColor)
        else:
            self._c1 = np.array(to_rgb(colors[0]))
            self._c2 = np.array(to_rgb(colors[1]))
            self.valueChanged.connect(self._setColor)

    @pyqtSlot(float)
    def _setColor(self, value):
        f = (value - self.minimum())/(self.maximum() - self.minimum())
        color = to_hex((1-f)*self._c1 + f*self._c2)
        style = (f'QDoubleSpinBox {{'
                 f' background-color: {color};'
                 f' selection-background-color: {color}; }}')
        self.ui.value.setStyleSheet(style)


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
