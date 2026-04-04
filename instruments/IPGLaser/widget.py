from qtpy import QtCore
from QInstrument.lib.QInstrumentWidget import QInstrumentWidget
from QInstrument.instruments.IPGLaser.instrument import QIPGLaser


class QIPGLaserWidget(QInstrumentWidget):
    '''Control widget for an IPG fiber laser.

    Displays keyswitch, aiming beam, emission, output power, and
    fault status. Polls the instrument every 500 ms to refresh
    read-only status fields.
    '''

    UIFILE = 'IPGLaserWidget.ui'
    poll_interval = 500  # ms

    def __init__(self, *args, device=None, **kwargs):
        device = device or QIPGLaser().find()
        super().__init__(*args, device=device, **kwargs)
        self._timer = QtCore.QTimer(self)
        self._timer.setInterval(self.poll_interval)
        self._timer.timeout.connect(self._poll)
        if self.device is not None and self.device.isOpen():
            self._timer.start()

    @QtCore.Slot()
    def _poll(self):
        for prop in ('keyswitch', 'power', 'fault', 'aiming', 'emission'):
            self.set(prop)


if __name__ == '__main__':
    QIPGLaserWidget.example()

__all__ = ['QIPGLaserWidget']
