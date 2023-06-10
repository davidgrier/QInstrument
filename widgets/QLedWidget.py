from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import (QByteArray, QPointF, QRectF, QTimer,
                          pyqtProperty, pyqtSlot)
from PyQt5.QtGui import QPainter
from PyQt5.QtSvg import QSvgRenderer
from enum import Enum
from pathlib import Path


class Color(Enum):
    RED = 1
    AMBER = 2
    GREEN = 3
    BLUE = 4
    VIOLET = 5
    WHITE = 6


class State(Enum):
    OFF = 0
    ON = 1


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

    RED = Color.RED
    AMBER = Color.AMBER
    GREEN = Color.GREEN
    BLUE = Color.BLUE
    VIOLET = Color.VIOLET
    WHITE = Color.WHITE

    OFF = State.OFF
    ON = State.ON

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
                         ON:  ('d0d0dd', 'f0f0ff')}
    }

    def __init__(self, *args,
                 color=None,
                 state=None,
                 blink=None,
                 interval=None,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self.setMinimumSize(48, 48)
        self.sizePolicy().setWidthForHeight(True)
        self.renderer = QSvgRenderer()
        self.timer = QTimer()
        self.timer.timeout.connect(self.flipState)
        self.template = self._load_template()
        self.color = color or self.RED
        self.state = state or self.ON
        self._savedstate = self.state
        self.blink = blink or False
        self.interval = interval or 400

    def __setattr__(self, name, value):
        super().__setattr__(name, value)
        if name in ['color', 'state']:
            self.update()

    def _load_template(self):
        svgfile = Path(__file__).parent / 'QLedWidget.svg'
        with open(svgfile, 'r') as f:
            template = f.read()
        return template

    @pyqtProperty(bool)
    def blink(self):
        return self._blink

    @blink.setter
    def blink(self, blink):
        self._blink = blink
        if blink:
            self._savedstate = self.state
            self.timer.start(self.interval)
        else:
            self.timer.stop()
            self.state = self._savedstate

    @pyqtSlot()
    def flipState(self):
        self.state = self.OFF if self.state == self.ON else self.ON

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
    led.show()
    led.color = led.WHITE
    led.blink = True
    app.exec()


if __name__ == '__main__':
    example()
