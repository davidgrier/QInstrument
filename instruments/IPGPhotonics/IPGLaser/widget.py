from qtpy import QtCore
from QInstrument.lib.QInstrumentWidget import QInstrumentWidget
from QInstrument.instruments.IPGLaser.instrument import QIPGLaser
from QInstrument.widgets.QLedWidget import QLedWidget
from QInstrument.widgets.QRotaryEncoderSpinBox import QRotaryEncoderSpinBox


class QIPGLaserWidget(QInstrumentWidget):
    '''Control widget for an IPG fiber laser.

    Displays power-supply, keyswitch, and fault status as LED indicators.
    The fault LED blinks while a fault condition is active.  Aiming beam
    and emission status are shown as red LEDs; the adjacent push-buttons
    toggle each state.  Diode current is set with a rotary encoder
    spinbox.  Output power is shown as a read-only display.

    The widget polls the instrument every :attr:`poll_interval` ms to
    refresh all status fields.
    '''

    UIFILE = 'IPGLaserWidget.ui'
    INSTRUMENT = QIPGLaser
    poll_interval = 500  # ms

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

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._timer = QtCore.QTimer(self)
        self._timer.setInterval(self.poll_interval)
        self._timer.timeout.connect(self._poll)
        if self.device is not None and self.device.isOpen():
            self._setupControls()
            self._timer.start()

    def _setupControls(self) -> None:
        '''Configure LED colors and rotary encoder range from device state.

        Called once after the device is confirmed open.  Sets LED colors
        (``power_supply`` and ``keyswitch`` green; ``fault`` amber;
        ``aiming`` and ``emission`` red) and initialises the ``current``
        spinbox range from ``minimum_current`` and ``maximum_current``.
        '''
        self.power_supply.color = QLedWidget.GREEN
        self.keyswitch.color    = QLedWidget.GREEN
        self.fault.color        = QLedWidget.AMBER
        self.aiming.color       = QLedWidget.RED
        self.emission.color     = QLedWidget.RED
        self.current.setSingleStep(0.5)
        self.current.setTitle('Current [%]')
        self._updateCurrentRange()

    def _updateCurrentRange(self) -> None:
        '''Apply ``minimum_current`` and ``maximum_current`` to the spinbox.

        Called at setup and again after the first show event so that a
        ``maximum_current`` restored from the saved configuration is
        reflected in the spinbox bounds.
        '''
        min_c = float(self.device.get('minimum_current') or 0.)
        max_c = float(self.device.get('maximum_current') or 100.)
        self.current.setMinimum(min_c)
        self.current.setMaximum(max_c)

    def showEvent(self, event) -> None:
        '''Re-apply current range after the first-show config restore.'''
        super().showEvent(event)
        if self.device is not None and self.device.isOpen():
            self._updateCurrentRange()

    def _connectSignals(self) -> None:
        '''Connect widget signals to the device and wire the toggle buttons.

        Extends the base-class connection logic to manually connect the
        non-bound ``aiming_button`` and ``emission_button`` push-buttons
        to their respective toggle slots.
        '''
        super()._connectSignals()
        self.aiming_button.clicked.connect(self._toggleAiming)
        self.emission_button.clicked.connect(self._toggleEmission)

    @QtCore.Slot()
    def _toggleAiming(self) -> None:
        '''Toggle the aiming beam on or off.'''
        self.device.set('aiming', not bool(self.device.get('aiming')))

    @QtCore.Slot()
    def _toggleEmission(self) -> None:
        '''Toggle laser emission on or off.'''
        self.device.set('emission', not bool(self.device.get('emission')))

    @QtCore.Slot()
    def _poll(self) -> None:
        '''Read all polled status properties and update the UI.

        Calls :meth:`device.status` once per poll interval to minimise
        serial traffic, then updates each named widget.  The ``fault``
        LED is set to blink while a fault condition is active.
        '''
        for prop, value in self.device.status().items():
            widget = self.__dict__.get(prop)
            if widget is None:
                continue
            if prop == 'fault' and isinstance(widget, QLedWidget):
                # Stop any existing blink, set the correct state, then
                # re-enable blinking only when a fault is active.
                widget.blink = False
                widget.state = QLedWidget.ON if value else QLedWidget.OFF
                if value:
                    widget.blink = True
                continue
            setter = self._wmethod(widget, self.wsetter)
            if setter is None:
                continue
            widget.blockSignals(True)
            setter(value)
            widget.blockSignals(False)


if __name__ == '__main__':
    QIPGLaserWidget.example()

__all__ = ['QIPGLaserWidget']
