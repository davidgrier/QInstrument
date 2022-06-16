from QInstrument.lib.QFakeInstrument import (QFakeInstrument, Property)


class QFakeDS345(QFakeInstrument):

    amplitude = Property(1.)
    frequency = Property(1.)
    offset = Property(0.)
    phase = Property(0.)
    waveform = Property(0)
    invert = Property(False)
    mute = Property(False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.identification = 'Fake DS345 Function Generator'

