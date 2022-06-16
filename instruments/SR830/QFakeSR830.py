from QInstrument.lib.QFakeInstrument import (QFakeInstrument, Property)
import numpy as np


class QFakeSR830(QFakeInstrument):

    amplitude = Property(0.)
    frequency = Property(0.)
    harmonic = Property(1)
    internal_reference = Property(False)
    phase = Property(0.)
    reference_trigger = Property(0)
    dc_coupling = Property(True)
    input_configuration = Property(0)
    line_filter = Property(0)
    dynamic_reserve = Property(0)
    low_pass_slope = Property(0)
    sensitivity = Property(0)
    synchronous_filter = Property(False)
    time_constant = Property(0)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, *kwargs)
        self.identification = 'Fake SR830 Lockin Amplifier'

    def report(self):
        return np.random.rand(3).tolist()
