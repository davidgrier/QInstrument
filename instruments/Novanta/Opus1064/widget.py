from QInstrument.instruments.Novanta.Opus.widget import QOpusWidget
from QInstrument.instruments.Novanta.Opus1064.instrument import QOpus1064


class QOpus1064Widget(QOpusWidget):
    '''Control widget for a Novanta Opus1064 laser (1064 nm, 2–10 W).'''

    INSTRUMENT = QOpus1064


if __name__ == '__main__':
    QOpus1064Widget.example()

__all__ = ['QOpus1064Widget']
