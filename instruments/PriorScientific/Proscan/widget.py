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
    HARDWARE_DOMINANT = True

    def __init__(self, *args,
                 interval: int | None = None, **kwargs) -> None:
        '''Initialize the widget.

        Parameters
        ----------
        interval : int or None, optional
            Poll interval in milliseconds for position and limit updates.
            Overrides :attr:`QProscan.POLL_INTERVAL`. Default: 200.
        '''
        super().__init__(*args, **kwargs)
        self._interval = int(interval or 200)
        self._prev_limits = None
        self.joystick.setRange(-200., 200.)

    def _connectSignals(self) -> None:
        super()._connectSignals()
        self.joystick.positionChanged.connect(self._updateVelocity)
        self.joystick.stepped.connect(self._onStep)
        self.zdial.stepUp.connect(self.device.stepUp)
        self.zdial.stepDown.connect(self.device.stepDown)
        self.stop.clicked.connect(self.device.stop)
        self.set_origin.clicked.connect(self.device.set_origin)
        self.advancedToggle.toggled.connect(self._onAdvancedToggled)
        self.advanced.setVisible(False)
        self.device.positionChanged.connect(self._onPositionChanged)
        self.device.limitsChanged.connect(self._onLimitsChanged)

    def _firstShow(self) -> None:
        super()._firstShow()
        self.device.POLL_INTERVAL = self._interval
        QtCore.QMetaObject.invokeMethod(
            self.device, 'startPolling',
            QtCore.Qt.ConnectionType.QueuedConnection)

    @QtCore.Slot(bool)
    def _onAdvancedToggled(self, checked: bool) -> None:
        '''Show or hide the advanced settings panel.'''
        self.advanced.setVisible(checked)
        self.advancedToggle.setText(
            '▾ Advanced Settings' if checked else '▸ Advanced Settings')
        self.window().adjustSize()

    def showEvent(self, event: object) -> None:
        super().showEvent(event)
        self.window().adjustSize()

    @QtCore.Slot(object)
    def _onPositionChanged(self, pos: list[int]) -> None:
        '''Update the XYZ position displays.'''
        try:
            x, y, z = pos
        except (TypeError, ValueError):
            return
        self.x.display(x)
        self.y.display(y)
        self.z.display(z)

    @QtCore.Slot(object)
    def _onLimitsChanged(self, limits: object) -> None:
        '''Update limit-switch indicator styles and log new activations.'''
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
