from __future__ import annotations

import logging
from pathlib import Path
from qtpy import QtCore
from QInstrument.lib.QInstrumentWidget import QInstrumentWidget
from QInstrument.instruments.PriorScientific.Proscan.instrument import QProscan

logger = logging.getLogger(__name__)


_NORMAL_STYLE = 'background: lightyellow;'
_LIMIT_STYLE = 'background: #FF6B6B;'


class QProscanWidget(QInstrumentWidget):
    '''Control widget for the Prior Scientific Proscan stage controller.

    Displays the current XY and Z position, provides a joystick for
    continuous XY motion, a rotary encoder for Z focus, and spinboxes
    for speed, acceleration, and step-size settings.

    Position displays turn red when the corresponding axis limit switch
    is active.
    '''

    UIFILE = str(Path(__file__).parent / 'ProscanWidget.ui')
    INSTRUMENT = QProscan

    def __init__(self, *args, interval: int | None = None, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.joystick.setRange(-200., 200.)
        self._prev_limits = None
        self._timer = QtCore.QTimer(self)
        self._timer.timeout.connect(self._poll)
        if self.device is not None and self.device.isOpen():
            self._timer.start(interval or 200)

    def _connectSignals(self) -> None:
        super()._connectSignals()
        self.joystick.positionChanged.connect(self._updateVelocity)
        self.joystick.stepped.connect(self._onStep)
        self.zdial.stepUp.connect(self.device.stepUp)
        self.zdial.stepDown.connect(self.device.stepDown)
        self.stop.clicked.connect(self.device.stop)
        self.set_origin.clicked.connect(self.device.set_origin)

    @QtCore.Slot()
    def _poll(self) -> None:
        '''Query and display the current stage position and limit status.'''
        try:
            x, y, z = self.device.position()
            limits = self.device.active_limits()
        except (ValueError, TypeError):
            return
        self.x.display(x)
        self.y.display(y)
        self.z.display(z)
        if limits and not self._prev_limits:
            logger.warning(
                f'Limit switch active: X={limits[0]}, '
                f'Y={limits[1]}, Z={limits[2]}')
        self._prev_limits = limits
        x_hit, y_hit, z_hit, _ = limits or (False, False, False, False)
        self.x.setStyleSheet(_LIMIT_STYLE if x_hit else _NORMAL_STYLE)
        self.y.setStyleSheet(_LIMIT_STYLE if y_hit else _NORMAL_STYLE)
        self.z.setStyleSheet(_LIMIT_STYLE if z_hit else _NORMAL_STYLE)

    @QtCore.Slot(str)
    def _onStep(self, direction: str) -> None:
        '''Execute one discrete step in *direction*.'''
        methods = {
            'left':  self.device.stepLeft,
            'right': self.device.stepRight,
            'up':    self.device.stepForward,
            'down':  self.device.stepBackward,
        }
        methods[direction]()

    @QtCore.Slot(object)
    def _updateVelocity(self, velocity: object) -> None:
        '''Forward joystick position to the stage as a velocity command.'''
        logger.debug(f'velocity: {velocity}')
        self.device.set_velocity(velocity)


__all__ = ['QProscanWidget']


if __name__ == '__main__':
    QProscanWidget.example()
