from PyQt5.QtCore import (QObject, pyqtProperty)
import types


class QInstrument(QObject):

    def __str__(self):
        name = self.__class__.__name__
        s = f'{name}(settings=settings)'
        for k, v in self.settings:
            s += f'\n\t{k}={v}'
        return s

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.interface = None

    @pyqtProperty(QObject)
    def interface(self):
        return self._interface

    def open(self, **kwargs):
        self._interface.open(**kwargs)

    def close(self):
        self._interface.close()

    def transmit(self, data):
        self._interface.transmit(data)

    def receive(self, **kwargs):
        return self._interface.receive(**kwargs)

    def identify(self, **kwargs):
        return False

    def find(self, **kwargs):
        return self

    def handshake(self, data, **kwargs):
        '''Transmit data to the instrument and receive its response

        Arguments
        ---------
        data: str
            String to be transmitted to the instrument
            to elicit a response

        Keywords
        --------
        Keywords are passed through to receive()

        Returns
        -------
        response:
            Response from instrument
        '''
        self.transmit(self, data)
        return self.receive(**kwargs)

    def expect(self, query, response, **kwargs):
        return response in self.handshake(query, **kwargs)

    @pyqtProperty(list)
    def properties(self):
        '''List of instrument properties'''
        print('getting')
        kv = vars(type(self)).items()
        return [k for k, v in kv if isinstance(v, pyqtProperty)]

    def methods(self):
        '''List of instrument methods'''
        kv = vars(type(self)).items()
        return [k for k, v in kv if isinstance(v, types.FunctionType)]

    @pyqtProperty(dict)
    def settings(self):
        plist = self.properties
        print(len(plist))
        return {p: getattr(self, p) for p in plist}

    @settings.setter
    def settings(self, settings):
        for key, value in settings.items():
            if hasattr(self, key):
                setattr(self, key, value)
