from QInstrument.instruments.Novanta.Opus.fake import QFakeOpus
from QInstrument.instruments.Novanta.Opus660.instrument import QOpus660


class QFakeOpus660(QFakeOpus, QOpus660):
    '''Fake Opus660 laser for UI development without hardware.'''


__all__ = ['QFakeOpus660']
