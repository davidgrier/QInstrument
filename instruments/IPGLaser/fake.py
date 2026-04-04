from QInstrument.lib.QFakeInstrument import QFakeInstrument


class QFakeIPGLaser(QFakeInstrument):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._keyswitch = True
        self._aiming = False
        self._emission = False
        self._power = 0.
        self._fault = False
        self.registerProperty('keyswitch', ptype=bool, setter=None)
        self.registerProperty('aiming', ptype=bool)
        self.registerProperty('emission', ptype=bool)
        self.registerProperty('power', ptype=float, setter=None)
        self.registerProperty('fault', ptype=bool, setter=None)
        self.identification = 'Fake IPG Fiber Laser'

__all__ = ['QFakeIPGLaser']
