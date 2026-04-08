from __future__ import annotations

import logging
from pathlib import Path
from qtpy import QtCore
from QInstrument.lib.QInstrumentWidget import QInstrumentWidget
from QInstrument.instruments.PiezoDrive.instrument import QPDUS210

logger = logging.getLogger(__name__)


class QPDUS210Widget(QInstrumentWidget):
    '''Control widget for the PiezoDrive PDUS210 ultrasonic amplifier.

    Displays measured values (current, voltage, frequency, impedance, phase,
    load power, amplifier power, temperature) and provides controls for
    setpoints and tracking modes.  Polls the instrument at a fixed interval.
    '''

    UIFILE = str(Path(__file__).parent / 'PDUS210Widget.ui')
    INSTRUMENT = QPDUS210

    def __init__(self, *args, interval: int | None = None, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._timer = QtCore.QTimer(self)
        self._timer.timeout.connect(self._poll)
        if self.device is not None and self.device.isOpen():
            self._timer.start(interval or 200)

    @QtCore.Slot()
    def _poll(self) -> None:
        '''Query and display all measured values.'''
        for name in ('current', 'loadPower', 'amplifierPower',
                     'frequency', 'impedance', 'phase', 'temperature'):
            self.device.get(name)


__all__ = ['QPDUS210Widget']


if __name__ == '__main__':
    QPDUS210Widget.example()
