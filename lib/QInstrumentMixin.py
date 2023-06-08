from PyQt5.QtCore import pyqtProperty
import types


class QInstrumentMixin(object):

    def __str__(self):
        name = self.__class__.__name__
        s = f'{name}'
        tab = (len(s) + 1) * ' '
        for k, v in self.settings.items():
            s += f'^{k}={v}$'
        s = s.replace('$^', ',\n'+tab)
        s = s.replace('^', '(')
        s = s.replace('$', ')')
        return s

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
        self.transmit(data)
        return self.receive(**kwargs)

    def expect(self, query, response, **kwargs):
        return response in self.handshake(query, **kwargs)

    @pyqtProperty(list)
    def properties(self):
        '''List of instrument properties'''
        kv = vars(type(self)).items()
        return [k for k, v in kv if isinstance(v, pyqtProperty)]

    def methods(self):
        '''List of instrument methods'''
        kv = vars(type(self)).items()
        return [k for k, v in kv if isinstance(v, types.FunctionType)]

    @pyqtProperty(dict)
    def settings(self):
        plist = self.properties
        return {p: getattr(self, p) for p in plist}

    @settings.setter
    def settings(self, settings):
        for key, value in settings.items():
            if hasattr(self, key):
                setattr(self, key, value)
