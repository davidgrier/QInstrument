from QInstrument.instruments.Novanta.Opus.widget import QOpusWidget
from QInstrument.instruments.Novanta.Opus532.instrument import QOpus532


class QOpus532Widget(QOpusWidget):
    '''Control widget for a Novanta Opus532 laser (532 nm, 0–6 W).'''

    INSTRUMENT = QOpus532


if __name__ == '__main__':
    QOpus532Widget.example()

__all__ = ['QOpus532Widget']
