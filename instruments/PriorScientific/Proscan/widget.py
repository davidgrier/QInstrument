from __future__ import annotations

import logging
from pathlib import Path
from qtpy import QtCore
from QInstrument.lib.QInstrumentWidget import QInstrumentWidget
from QInstrument.instruments.PriorScientific.Proscan.instrument import QProscan

logger = logging.getLogger(__name__)


class QProscanWidget(QInstrumentWidget):
    '''Control widget for the Prior Scientific Proscan stage controller.

    Displays the current XY and Z position, provides a joystick for
    continuous XY motion, a rotary encoder for Z focus, and spinboxes
    for speed, acceleration, and step-size settings.
    '''

    UIFILE = str(Path(__file__).parent / 'ProscanWidget.ui')
    INSTRUMENT = QProscan

    def __init__(self, *args, interval: int | None = None, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.joystick.setRange(-200., 200.)
        self._timer = QtCore.QTimer(self)
        self._timer.timeout.connect(self._poll)
        if self.device is not None and self.device.isOpen():
            self._timer.start(interval or 200)

    def _connectSignals(self) -> None:
        super()._connectSignals()
        self.joystick.positionChanged.connect(self._updateVelocity)
        self.zdial.stepUp.connect(self.device.stepUp)
        self.zdial.stepDown.connect(self.device.stepDown)
        self.stop.clicked.connect(self.device.stop)
        self.set_origin.clicked.connect(self.device.set_origin)

    @QtCore.Slot()
    def _poll(self) -> None:
        '''Query and display the current stage position.'''
        try:
            x, y, z = self.device.position()
        except (ValueError, TypeError):
            return
        self.x.display(x)
        self.y.display(y)
        self.z.display(z)

    @QtCore.Slot(object)
    def _updateVelocity(self, velocity: object) -> None:
        '''Forward joystick position to the stage as a velocity command.'''
        logger.debug(f'velocity: {velocity}')
        self.device.set_velocity(velocity)

__all__ = ['QProscanWidget']


if __name__ == '__main__':
    QProscanWidget.example()
