from PyQt5.QtCore import QThread


def threadedInstrument(cls):

    class ThreadedInstrument(cls):
        __name__ = cls.__name__
        __qualname__ = cls.__qualname__
        __doc__ = cls.__doc__

        def __init__(self, *args, **kwargs):
            super().__init__(*args, *kwargs)
            self._thread = QThread(self)
            self.device.moveToThread(self._thread)

        def closeEvent(self, event):
            self._thread.quit()
            self._thread.wait()
            del self._thread
            del self._device
            super().closeEvent(event)
            event.accept()

    return ThreadedInstrument
