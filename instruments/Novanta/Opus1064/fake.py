from QInstrument.instruments.Novanta.Opus.fake import QFakeOpus
from QInstrument.instruments.Novanta.Opus1064.instrument import QOpus1064


class QFakeOpus1064(QFakeOpus, QOpus1064):
    '''Fake Opus1064 laser for UI development without hardware.'''


__all__ = ['QFakeOpus1064']
