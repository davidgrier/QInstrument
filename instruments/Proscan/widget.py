from __future__ import annotations

import sys
import logging
from pathlib import Path
from qtpy import QtCore, QtWidgets
from QInstrument.lib.QInstrumentWidget import QInstrumentWidget
from QInstrument.instruments.Proscan.instrument import QProscan
from QInstrument.instruments.Proscan.fake import QFakeProscan

logger = logging.getLogger(__name__)


class QProscanWidget(QInstrumentWidget):
    '''Control widget for the Prior Scientific Proscan stage controller.

    Displays the current XY and Z position, provides a joystick for
    continuous XY motion, a rotary encoder for Z focus, and spinboxes
    for speed, acceleration, and step-size settings.
    '''

    UIFILE = str(Path(__file__).parent / 'ProscanWidget.ui')
    FAKEDEVICE = QFakeProscan

    def __init__(self, *args, device: QProscan | None = None,
                 interval: int | None = None, **kwargs) -> None:
        super().__init__(*args, device=device, **kwargs)
        self.joystick.setRange(-200., 200.)
        self._interval = interval or 200
        self._timer = QtCore.QTimer(self)
        self._connectSignals()
        self._timer.start(self._interval)

    def _connectSignals(self) -> None:
        super()._connectSignals()
        self.joystick.positionChanged.connect(self._updateVelocity)
        self.zdial.stepUp.connect(self.device.stepUp)
        self.zdial.stepDown.connect(self.device.stepDown)
        self.stop.clicked.connect(self.device.stop)
        self.set_origin.clicked.connect(self.device.set_origin)
        self._timer.timeout.connect(self._poll)

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

    @classmethod
    def example(cls) -> None:
        app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
        device = QProscan().find() or QFakeProscan()
        widget = cls(device=device)
        widget.show()
        sys.exit(app.exec())


__all__ = ['QProscanWidget']


if __name__ == '__main__':
    QProscanWidget.example()
