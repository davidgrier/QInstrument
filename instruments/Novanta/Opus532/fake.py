from QInstrument.instruments.Novanta.Opus.fake import QFakeOpus
from QInstrument.instruments.Novanta.Opus532.instrument import QOpus532


class QFakeOpus532(QFakeOpus, QOpus532):
    '''Fake Opus532 laser for UI development without hardware.'''


__all__ = ['QFakeOpus532']
