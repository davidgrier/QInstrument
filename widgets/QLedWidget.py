from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import (QByteArray, QPointF, QRectF, QTimer,
                          pyqtProperty, pyqtSlot)
from PyQt5.QtGui import QPainter
from PyQt5.QtSvg import QSvgRenderer
import os
import sys


class QLedWidget(QWidget):

    Red = 1
    Amber = 2
    Green = 3
    Blue = 4
    Violet = 5

    Off = 1
    On = 2

    hexcodes = {Red:    {Off: ('#3f0000', '#a00000'),
                         On:  ('#af0000', '#ff0f0f')},
                Amber:  {Off: ('#aa4400', '#ad892c'),
                         On:  ('#d45500', '#ffd42a')},
                Green:  {Off: ('#001c00', '#008200'),
                         On:  ('#009400', '#00d700')},
                Blue:   {Off: ('#102151', '#0a163c'),
                         On:  ('#082686', '#0342eb')},
                Violet: {Off: ('#45098f', '#471b7d'),
                         On:  ('#5a00cc', '#a65fff')}}

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
        self.color = color or self.Red
        self.state = state or self.On
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

    @pyqtSlot()
    def flipState(self):
        self.state = self.On if self.state is self.Off else self.Off
            
    def _get_template(self):
        file = sys.modules[self.__module__].__file__
        dir = os.path.dirname(os.path.abspath(file))
        path = os.path.join(dir, 'QLedWidget.txt')
        with open(path, 'r') as f:
            template = f.read()
        return template

    def _connectSignals(self):
        self.timer.timeout.connect(self.flipState)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        bounds = QRectF(0., 0., self.size().width(), self.size().height())
        hexcodes = self.hexcodes[self.color][self.state]
        _xml = self.template.format(*hexcodes).encode('utf-8')
        self.renderer.load(QByteArray(_xml))
        self.renderer.render(painter, self._bounds())

    def _bounds(self):
        x, y = self.size().width()/2., self.size().height()/2.
        dim = min(x, y)
        return QRectF(QPointF(x-dim, y-dim), QPointF(x+dim, y+dim))
        


if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    widget = QLedWidget()
    widget.color = QLedWidget.Blue
    widget.blink = True
    widget.show()
    sys.exit(app.exec_())
