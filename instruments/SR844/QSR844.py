from QInstrument.instruments.SR830 import QSR830


class QSR844(QSR830):

    def identify(self):
        return 'SR844' in self.handshake('*IDN?')
