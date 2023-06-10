from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import (QByteArray, QPointF, QRectF, QTimer,
                          pyqtProperty, pyqtSlot)
from PyQt5.QtGui import QPainter
from PyQt5.QtSvg import QSvgRenderer
from pathlib import Path


class QLedWidget(QWidget):
    '''LED indicator

    ...

    Inherits
    --------
    PyQt5.QtWidgets.QWidget

    Properties
    ==========

    Colors
    ------
    RED, AMBER, GREEN, BLUE, VIOLET, WHITE

    States
    ------
    ON, OFF

    color: Colors
        Color of the LED indicator
    state: States
        ON: LED is bright
        OFF: LED is dark
    blink: bool
        True: LED alternates between ON and OFF
        False: LED returns to its initial state
    interval: int
        Duration of each state during blinking
        in milliseconds
    '''

    RED = 1
    AMBER = 2
    GREEN = 3
    BLUE = 4
    VIOLET = 5
    WHITE = 6

    OFF = False
    ON = True

    hexcodes = {RED:    {OFF: ('3f0000', 'a00000'),
                         ON:  ('af0000', 'ff0f0f')},
                AMBER:  {OFF: ('aa4400', 'ad892c'),
                         ON:  ('d45500', 'ffd42a')},
                GREEN:  {OFF: ('001c00', '008200'),
                         ON:  ('009400', '00d700')},
                BLUE:   {OFF: ('102151', '0a163c'),
                         ON:  ('082686', '0342eb')},
                VIOLET: {OFF: ('45098f', '471b7d'),
                         ON:  ('5a00cc', 'a65fff')},
                WHITE:  {OFF: ('505055', 'a0a0aa'),
                         ON:  ('d0d0dd', 'f0f0ff')}}

    SVG_FILE = 'QLedWidget.svg'

    def __init__(self, *args,
                 color=None,
                 state=None,
                 blink=None,
                 interval=None,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self.setMinimumSize(48, 48)
        self.sizePolicy().setWidthForHeight(True)
        self.template = self._get_template()
        self.renderer = QSvgRenderer()
        self.timer = QTimer()
        self.color = color or self.RED
        self.state = state or self.ON
        self.blink = blink or False
        self.interval = interval or 400
        self._connectSignals()

    @pyqtProperty(int)
    def color(self):
        return self._color

    @color.setter
    def color(self, value):
        self._color = value
        self.update()

    @pyqtProperty(int)
    def state(self):
        return self._state

    @state.setter
    def state(self, value):
        self._state = value
        self._setstate = value
        self.update()

    @pyqtProperty(bool)
    def blink(self):
        return self._blink

    @blink.setter
    def blink(self, blink):
        self._blink = blink
        if blink:
            self.timer.start(self.interval)
        else:
            self.timer.stop()
            self.state = self._setstate

    @pyqtProperty(int)
    def interval(self):
        return self._interval

    @interval.setter
    def interval(self, value):
        self._interval = abs(value)

    @pyqtSlot()
    def flipState(self):
        self.state = not self.state
#        self.state = self.ON if self.state is self.OFF else self.OFF

    def _get_template(self):
        path = Path(__file__).parent / self.SVG_FILE
        with open(path, 'r') as f:
            template = f.read()
        return template

    def _connectSignals(self):
        self.timer.timeout.connect(self.flipState)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        a, b = self.hexcodes[self.color][self.state]
        svg = self.template.replace('af0000', a).replace('ff0f0f', b)
        self.renderer.load(QByteArray(svg.encode()))
        self.renderer.render(painter, self._bounds())

    def _bounds(self):
        x, y = self.size().width()/2., self.size().height()/2.
        dim = min(x, y)
        return QRectF(QPointF(x-dim, y-dim), QPointF(x+dim, y+dim))


def example():
    from PyQt5.QtWidgets import QApplication

    app = QApplication([])
    led = QLedWidget()
    led.color = led.WHITE
    led.blink = True
    led.show()
    app.exec()


if __name__ == '__main__':
    example()
