from PyQt5.QtCore import (QObject, pyqtProperty)
import logging


logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class Property(pyqtProperty):

    def __init__(self, value, name=''):
        super().__init__(type(value), self.getter, self.setter)
        self.value = value
        self.name = name

    def getter(self, inst=None):
        return self.value

    def setter(self, inst=None, value=None):
        logger.debug(f'Setting {self.name}: {value}')
        self.value = value


class PropertyMeta(type(QObject)):
    def __new__(mcs, name, bases, attrs):
        for key in list(attrs.keys()):
            attr = attrs[key]
            if not isinstance(attr, Property):
                continue
            value = attr.value
            attrs[key] = Property(value, key)
        return super().__new__(mcs, name, bases, attrs)


class QFakeInstrument(QObject, metaclass=PropertyMeta):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.identification = 'Fake Instrument'

    def busy(self):
        return False

    def isOpen(self):
        return True
