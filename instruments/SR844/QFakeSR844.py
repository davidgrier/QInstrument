from QInstrument.instruments.SR830 import QFakeSR830


class QFakeSR844(QFakeSR830):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, *kwargs)
        self.identification = 'Fake SR844 Lockin Amplifier'
