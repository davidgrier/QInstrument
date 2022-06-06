from PyQt5.QtCore import QThread
from QInstrument.lib import QInstrumentWidget


class QThreadedInstrumentWidget(QInstrumentWidget):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._thread = QThread(self)
        self.device.moveToThread(self._thread)

    def closeEvent(self, event):
        self._thread.quit()
        self._thread.wait()
        del self._thread
        del self._device
        super().closeEvent(event)
        event.accept()
