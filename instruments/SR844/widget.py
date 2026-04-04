from QInstrument.lib.QInstrumentWidget import QInstrumentWidget
from QInstrument.instruments.SR844.instrument import QSR844


class QSR844Widget(QInstrumentWidget):
    '''Stanford Research Systems SR844 RF Lock-in Amplifier
    '''

    UIFILE = 'SR844Widget.ui'

    def __init__(self, *args, device=None, **kwargs):
        device = device or QSR844().find()
        super().__init__(*args, device=device, **kwargs)


if __name__ == '__main__':
    QSR844Widget.example()

__all__ = ['QSR844Widget']
