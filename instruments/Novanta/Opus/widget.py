from qtpy import QtCore
from QInstrument.lib.QInstrumentWidget import QInstrumentWidget
from QInstrument.instruments.Novanta.Opus.instrument import QOpus
from QInstrument.widgets.QLedWidget import QLedWidget
from QInstrument.widgets.QRotaryEncoderSpinBox import QRotaryEncoderSpinBox


class QOpusWidget(QInstrumentWidget):
    '''Control widget for a Laser Quantum Opus diode laser.

    Shows actual output power [W] and diode current [%] as read-only
    displays.  The requested power setpoint is controlled with a rotary
    encoder spinbox (in Watts; converted to mW for the instrument).
    Laser emission is toggled with a push-button; a red LED alongside
    the button reflects the current emission state.

    The widget polls the instrument every :attr:`poll_interval` ms to
    refresh the read-only displays and the emission indicator.
    '''

    UIFILE = 'OpusWidget.ui'
    poll_interval: int = 2000  # ms

    wsetter = QInstrumentWidget.wsetter | {
        'QLedWidget':            'setValue',
        'QRotaryEncoderSpinBox': 'setValue',
    }
    wgetter = QInstrumentWidget.wgetter | {
        'QLedWidget':            'value',
        'QRotaryEncoderSpinBox': 'value',
    }
    wsignal = QInstrumentWidget.wsignal | {
        'QRotaryEncoderSpinBox': 'valueChanged',
    }

    def __init__(self, *args, device=None, **kwargs) -> None:
        device = device or QOpus().find()
        super().__init__(*args, device=device, **kwargs)
        self._timer = QtCore.QTimer(self)
        self._timer.setInterval(self.poll_interval)
        self._timer.timeout.connect(self._poll)
        if self.device is not None and self.device.isOpen():
            self._setupControls()
            self._timer.start()

    def _setupControls(self) -> None:
        '''Configure the group box title, LED color, and power setpoint encoder.

        Called once after the device is confirmed open.  Updates the
        group box title with the device wavelength if available, sets the
        emission LED to red, configures the ``power_setpoint`` rotary
        encoder appearance, and applies the current ``maximum_power``
        as the encoder upper bound.
        '''
        wavelength = getattr(type(self.device), 'WAVELENGTH', None)
        if wavelength is not None:
            self.groupBox.setTitle(f'Opus {int(wavelength)} nm DPSS Laser')
        self.emission.color = QLedWidget.RED
        self.power_setpoint.setTitle('Power [W]')
        self.power_setpoint.setSingleStep(0.01)
        self.power_setpoint.setDecimals(3)
        self.power_setpoint.setColors(('white', '#68ff00'))
        self._updatePowerRange()

    def _updatePowerRange(self) -> None:
        '''Apply ``maximum_power`` [mW] to the power setpoint encoder [W].

        Called at setup and again after the first show event so that a
        ``maximum_power`` restored from the saved configuration is
        reflected in the encoder bounds.
        '''
        max_p = float(self.device.get('maximum_power') or 1000.)
        self.power_setpoint.setMinimum(0.)
        self.power_setpoint.setMaximum(max_p / 1000.)

    def showEvent(self, event) -> None:
        '''Re-apply power range after the first-show config restore.'''
        self._timer.stop()
        super().showEvent(event)
        if self.device is not None and self.device.isOpen():
            self._updatePowerRange()
            self._timer.start()

    def _connectSignals(self) -> None:
        '''Connect the emission toggle button and power setpoint encoder.

        Extends the base-class connection logic to manually wire the
        ``emission_button`` toggle and the ``power_setpoint`` encoder to
        their respective slots.
        '''
        super()._connectSignals()
        self.emission_button.clicked.connect(self._toggleEmission)
        self.power_setpoint.valueChanged.connect(self._setPower)

    @QtCore.Slot(float)
    def _setPower(self, value: float) -> None:
        '''Transmit a new power setpoint to the device.

        Parameters
        ----------
        value : float
            Requested power [W]; converted to mW before transmission.
        '''
        self.device.set('power', value * 1000.)

    @QtCore.Slot()
    def _toggleEmission(self) -> None:
        '''Toggle laser emission on or off.'''
        self.device.set('emission', not bool(self.device.get('emission')))

    @QtCore.Slot()
    def _poll(self) -> None:
        '''Read actual power, diode current, and emission state; update the UI.

        Converts the instrument power [mW] to Watts for the display.
        Only read-only status values are updated here; the power setpoint
        encoder is left untouched.
        '''
        power = self.device.get('power')
        if power is not None:
            self.power_display.blockSignals(True)
            self.power_display.setValue(float(power) / 1000.)
            self.power_display.blockSignals(False)

        current = self.device.get('current')
        if current is not None:
            self.current_display.blockSignals(True)
            self.current_display.setValue(float(current))
            self.current_display.blockSignals(False)

        emission = self.device.get('emission')
        if emission is not None:
            self.emission.blockSignals(True)
            self.emission.setValue(bool(emission))
            self.emission.blockSignals(False)


if __name__ == '__main__':
    QOpusWidget.example()

__all__ = ['QOpusWidget']
