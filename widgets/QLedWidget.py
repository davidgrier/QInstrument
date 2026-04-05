from __future__ import annotations

import sys
from enum import Enum
from pathlib import Path
from qtpy import QtCore, QtWidgets, QtGui, QtSvg


class QLedWidget(QtWidgets.QWidget):
    '''SVG-based LED indicator widget.

    Renders a colored LED that can be on, off, or blinking.

    Properties
    ==========
    blink : bool
        True: LED alternates between ON and OFF states at
        :attr:`interval` ms per state.
        False: LED returns to its saved state and stops blinking.
    color : QLedWidget.Color
        LED color.  One of ``RED``, ``AMBER``, ``GREEN``, ``BLUE``,
        ``VIOLET``, ``WHITE``.
    interval : int [ms]
        Duration of each ON/OFF phase during blinking. Default: 400.
    state : QLedWidget.State
        ``ON``: LED is bright. ``OFF``: LED is dark.
    '''

    class Color(Enum):
        RED    = 1
        AMBER  = 2
        GREEN  = 3
        BLUE   = 4
        VIOLET = 5
        WHITE  = 6

    class State(Enum):
        OFF = 0
        ON  = 1

    RED    = Color.RED
    AMBER  = Color.AMBER
    GREEN  = Color.GREEN
    BLUE   = Color.BLUE
    VIOLET = Color.VIOLET
    WHITE  = Color.WHITE

    OFF = State.OFF
    ON  = State.ON

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

    def __init__(self, *args,
                 color: Color | None = None,
                 state: State | None = None,
                 blink: bool | None = None,
                 interval: int | None = None,
                 **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.setMinimumSize(48, 48)
        self.sizePolicy().setWidthForHeight(True)
        self.renderer = QtSvg.QSvgRenderer()
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.flipState)
        self.template = self._load_template()
        self.color = color or self.RED
        self.state = state or self.ON
        self._savedstate = self.state
        self.blink = blink or False
        self.interval = interval or 400

    def __setattr__(self, name: str, value: object) -> None:
        super().__setattr__(name, value)
        if name in ('color', 'state'):
            self.update()

    def _load_template(self) -> str:
        '''Read and return the SVG template as a string.'''
        svgfile = Path(__file__).parent / 'QLedWidget.svg'
        with open(svgfile, 'r') as f:
            return f.read()

    @property
    def blink(self) -> bool:
        return self._blink

    @blink.setter
    def blink(self, blink: bool) -> None:
        self._blink = blink
        if blink:
            self._savedstate = self.state
            self.timer.start(self._interval)
        else:
            self.timer.stop()
            self.state = self._savedstate

    @property
    def interval(self) -> int:
        return self._interval

    @interval.setter
    def interval(self, ms: int) -> None:
        '''Set the blink interval.

        If the LED is currently blinking the timer is restarted
        immediately at the new interval.

        Parameters
        ----------
        ms : int
            Duration of each ON/OFF phase in milliseconds.
        '''
        self._interval = ms
        if self.timer.isActive():
            self.timer.start(ms)

    @QtCore.Slot()
    def flipState(self) -> None:
        '''Toggle the LED between ON and OFF states.'''
        self.state = self.OFF if self.state == self.ON else self.ON

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing, True)
        a, b = self.hexcodes[self.color][self.state]
        svg = self.template.replace('af0000', a).replace('ff0f0f', b)
        self.renderer.load(QtCore.QByteArray(svg.encode()))
        self.renderer.render(painter, self._bounds())

    def _bounds(self) -> QtCore.QRectF:
        x, y = self.size().width() / 2., self.size().height() / 2.
        dim = min(x, y)
        return QtCore.QRectF(QtCore.QPointF(x - dim, y - dim),
                             QtCore.QPointF(x + dim, y + dim))


def example() -> None:
    from qtpy.QtWidgets import QApplication

    app = QApplication.instance() or QApplication(sys.argv)
    led = QLedWidget()
    led.show()
    led.color = QLedWidget.WHITE
    led.blink = True
    sys.exit(app.exec())


__all__ = ['QLedWidget']


if __name__ == '__main__':
    example()
