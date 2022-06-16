from PyQt5.QtCore import (QObject, pyqtProperty)


class QFakeInstrument(QObject):

    def Property(pstr, default=0.):
        name = f'_{pstr}'
        vars()[name] = default
        dtype = type(default)

        def getter(self):
            return getattr(self, name)

        def setter(self, value):
            setattr(self, name, value)

        return pyqtProperty(dtype, getter, setter)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.identification = 'Fake Instrument'

    def busy(self):
        return False
