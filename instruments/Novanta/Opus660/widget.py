from QInstrument.instruments.Novanta.Opus.widget import QOpusWidget
from QInstrument.instruments.Novanta.Opus660.instrument import QOpus660


class QOpus660Widget(QOpusWidget):
    '''Control widget for a Novanta Opus660 laser (660 nm, 0–1.5 W).'''

    INSTRUMENT = QOpus660


if __name__ == '__main__':
    QOpus660Widget.example()

__all__ = ['QOpus660Widget']
