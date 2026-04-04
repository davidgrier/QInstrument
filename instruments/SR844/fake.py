import numpy as np
from QInstrument.lib.QFakeInstrument import QFakeInstrument


class QFakeSR844(QFakeInstrument):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._amplitude = 0.
        self._frequency = 0.
        self._harmonic = 1
        self._internal_reference = False
        self._phase = 0.
        self._reference_trigger = 0
        self._dc_coupling = True
        self._input_configuration = 0
        self._line_filter = 0
        self._dynamic_reserve = 0
        self._low_pass_slope = 0
        self._sensitivity = 0
        self._synchronous_filter = False
        self._time_constant = 0
        self.registerProperty('amplitude')
        self.registerProperty('frequency')
        self.registerProperty('harmonic', ptype=int)
        self.registerProperty('internal_reference', ptype=bool)
        self.registerProperty('phase')
        self.registerProperty('reference_trigger', ptype=int)
        self.registerProperty('dc_coupling', ptype=bool)
        self.registerProperty('input_configuration', ptype=int)
        self.registerProperty('line_filter', ptype=int)
        self.registerProperty('dynamic_reserve', ptype=int)
        self.registerProperty('low_pass_slope', ptype=int)
        self.registerProperty('sensitivity', ptype=int)
        self.registerProperty('synchronous_filter', ptype=bool)
        self.registerProperty('time_constant', ptype=int)
        self.identification = 'Fake SR844 RF Lockin Amplifier'

    def report(self):
        '''Return [frequency, amplitude, phase]'''
        data = np.random.rand(3)
        data[2] *= 360.
        return data.tolist()

__all__ = ['QFakeSR844']
