import logging
from qtpy import QtCore
from QInstrument.lib.QInstrumentWidget import QInstrumentWidget
from QInstrument.instruments.Opus.instrument import QOpus


logger = logging.getLogger(__name__)


class QOpusWidget(QInstrumentWidget):
    '''Control widget for a Laser Quantum Opus laser.

    Displays actual output power and diode current, and provides
    controls for the power setpoint and emission disable.  Polls
    the instrument every 200 ms to refresh the read-only displays.
    '''

    UIFILE = 'OpusWidget.ui'
    poll_interval: int = 200  # ms

    def __init__(self, *args, device=None, **kwargs) -> None:
        device = device or QOpus().find()
        super().__init__(*args, device=device, **kwargs)
        self._timer = QtCore.QTimer(self)
        self._timer.setInterval(self.poll_interval)
        self._timer.timeout.connect(self._poll)
        self._connectSignals()
        if self.device is not None and self.device.isOpen():
            self._timer.start()

    def _connectSignals(self) -> None:
        '''Connect UI widget signals to their handlers.'''
        self.PowerDial.valueChanged.connect(self._dialChanged)
        self.Power.editingFinished.connect(self._spinboxChanged)
        self.SendPower.clicked.connect(self._sendPower)
        self.Disable.clicked.connect(self._disable)

    @QtCore.Slot()
    def _poll(self) -> None:
        '''Read actual power and current from the device and update displays.'''
        power = self.device.get('power')
        if power is not None:
            self.ActualPower.blockSignals(True)
            self.ActualPower.setValue(power)
            self.ActualPower.blockSignals(False)
            self.EnableSwitch.blockSignals(True)
            self.EnableSwitch.setChecked(power > 0)
            self.EnableSwitch.blockSignals(False)
        current = self.device.get('current')
        if current is not None:
            self.CurrentBox.blockSignals(True)
            self.CurrentBox.setValue(current)
            self.CurrentBox.blockSignals(False)

    @QtCore.Slot(int)
    def _dialChanged(self, value: int) -> None:
        '''Sync the Power spinbox to the dial and clear the sent indicator.'''
        self.Power.blockSignals(True)
        self.Power.setValue(float(value))
        self.Power.blockSignals(False)
        self.sentCheck.blockSignals(True)
        self.sentCheck.setChecked(False)
        self.sentCheck.blockSignals(False)

    @QtCore.Slot()
    def _spinboxChanged(self) -> None:
        '''Sync the dial to the Power spinbox value.'''
        self.PowerDial.blockSignals(True)
        self.PowerDial.setValue(int(self.Power.value()))
        self.PowerDial.blockSignals(False)

    @QtCore.Slot()
    def _sendPower(self) -> None:
        '''Transmit the current Power spinbox value as the power setpoint.'''
        self.device.set('power', self.Power.value())
        self.sentCheck.blockSignals(True)
        self.sentCheck.setChecked(True)
        self.sentCheck.blockSignals(False)

    @QtCore.Slot()
    def _disable(self) -> None:
        '''Disable laser emission.'''
        self.device.set('emission', False)


if __name__ == '__main__':
    QOpusWidget.example()

__all__ = ['QOpusWidget']
