from QInstrument.lib.QFakeInstrument import QFakeInstrument


class QFakeDS345(QFakeInstrument):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._amplitude = 1.
        self._frequency = 1.
        self._offset = 0.
        self._phase = 0.
        self._waveform = 0
        self._invert = False
        self._mute = False
        self.registerProperty('amplitude')
        self.registerProperty('frequency')
        self.registerProperty('offset')
        self.registerProperty('phase')
        self.registerProperty('waveform', ptype=int)
        self.registerProperty('invert', ptype=bool)
        self.registerProperty('mute', ptype=bool)
        self.identification = 'Fake DS345 Function Generator'
