from __future__ import annotations

import sys
from enum import Enum
from qtpy import QtCore, QtWidgets, QtGui


class QLedWidget(QtWidgets.QWidget):
    '''LED indicator widget drawn with QPainter.

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
        RED = 1
        AMBER = 2
        GREEN = 3
        BLUE = 4
        VIOLET = 5
        WHITE = 6

    class State(Enum):
        OFF = 0
        ON = 1

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
                         ON:  ('d0d0dd', 'f0f0ff')}}

    def __init__(self, *args,
                 color: Color | None = None,
                 state: State | None = None,
                 blink: bool | None = None,
                 interval: int | None = None,
                 **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._setupUi()
        self.color = color or self.RED
        self.state = state or self.ON
        self._savedstate = self.state
        self.blink = blink or False
        self.interval = interval or 400

    def __setattr__(self, name: str, value: object) -> None:
        super().__setattr__(name, value)
        if name in ('color', 'state'):
            self.update()

    def _setupUi(self) -> None:
        self.setMinimumSize(16, 16)
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.flipState)

    def sizeHint(self) -> QtCore.QSize:
        return self.minimumSize()

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
    def interval(self, value: int) -> None:
        '''Set the blink interval.

        If the LED is currently blinking the timer is restarted
        immediately at the new interval.

        Parameters
        ----------
        value : int
            Duration of each ON/OFF phase [ms].
        '''
        self._interval = value
        if self.timer.isActive():
            self.timer.start(value)

    def value(self) -> bool:
        '''Return the LED state as a boolean.

        Returns
        -------
        bool
            ``True`` when the LED is :attr:`ON`
            ``False`` when :attr:`OFF`.
        '''
        return self.state == self.ON

    def setValue(self, value: bool) -> None:
        '''Set the LED state from a boolean value.

        Parameters
        ----------
        value : bool
            ``True`` to turn the LED :attr:`ON`; ``False`` for :attr:`OFF`.
        '''
        self.state = self.ON if value else self.OFF

    @QtCore.Slot()
    def flipState(self) -> None:
        '''Toggle the LED between ON and OFF states.'''
        self.state = self.OFF if self.state == self.ON else self.ON

    def changeEvent(self, event: QtCore.QEvent) -> None:
        '''Gray out the LED when disabled; restore color when re-enabled.

        When the widget (or any ancestor) is disabled, the LED switches
        to WHITE/OFF so it looks unpowered, consistent with the rest of
        the disabled instrument UI.  The original color, state, and blink
        are saved and restored when the widget is re-enabled.
        '''
        if event.type() == QtCore.QEvent.Type.EnabledChange:
            if not self.isEnabled():
                self._disabledColor = self.color
                self._disabledState = self.state
                self._disabledBlink = self.blink
                self.blink = False
                self.color = self.WHITE
                self.state = self.OFF
            else:
                self.color = self._disabledColor
                self.state = self._disabledState
                self.blink = self._disabledBlink
        super().changeEvent(event)

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        w, h = self.width(), self.height()
        size = min(w, h)
        cx, cy = w / 2., h / 2.
        r = size / 2.

        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        painter.setPen(QtCore.Qt.PenStyle.NoPen)

        # Outer bezel: silver metallic ring, lighter at top than bottom
        bezel = QtGui.QLinearGradient(cx, cy - r, cx, cy + r)
        bezel.setColorAt(0., QtGui.QColor('#f0f0f0'))
        bezel.setColorAt(1., QtGui.QColor('#adadad'))
        painter.setBrush(QtGui.QBrush(bezel))
        painter.drawEllipse(QtCore.QRectF(cx - r, cy - r, size, size))

        # Shadow ring: semi-transparent dark gray inside the bezel
        r2 = r * 0.808
        ring = QtGui.QRadialGradient(cx, cy, r2)
        ring.setColorAt(0., QtGui.QColor(0x92, 0x92, 0x92, 90))
        ring.setColorAt(1., QtGui.QColor(0x82, 0x82, 0x82, 200))
        painter.setBrush(QtGui.QBrush(ring))
        painter.drawEllipse(QtCore.QRectF(cx - r2, cy - r2, 2*r2, 2*r2))

        # LED body: color gradient lit from upper-left toward bottom-right
        r3 = r * 0.722
        a_hex, b_hex = self.hexcodes[self.color][self.state]
        led = QtGui.QLinearGradient(cx + r3, cy + r3,
                                    cx + r3 * 0.266, cy + r3 * 0.108)
        led.setColorAt(0., QtGui.QColor(f'#{a_hex}'))
        led.setColorAt(1., QtGui.QColor(f'#{b_hex}'))
        painter.setBrush(QtGui.QBrush(led))
        painter.drawEllipse(QtCore.QRectF(cx - r3, cy - r3, 2*r3, 2*r3))

        # Specular highlight: small white ellipse, upper-left of LED, rotated
        painter.save()
        painter.translate(cx - r * 0.312, cy - r * 0.408)
        painter.rotate(-34.3)
        r_a, r_b = r * 0.244, r * 0.149
        hl = QtGui.QLinearGradient(0., r_b, 0., -r_b * 0.7)
        hl.setColorAt(0., QtGui.QColor(255, 255, 255, 0))
        hl.setColorAt(1., QtGui.QColor(255, 255, 255, 220))
        painter.setBrush(QtGui.QBrush(hl))
        painter.drawEllipse(QtCore.QRectF(-r_a, -r_b, 2*r_a, 2*r_b))
        painter.restore()


def example() -> None:
    from qtpy.QtWidgets import QApplication

    app = QApplication.instance() or QApplication(sys.argv)
    led = QLedWidget()
    led.show()
    led.color = QLedWidget.RED
    led.blink = True
    sys.exit(app.exec())


__all__ = ['QLedWidget']


if __name__ == '__main__':
    example()
