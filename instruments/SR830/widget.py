from QInstrument.lib.QInstrumentWidget import QInstrumentWidget
from QInstrument.instruments.SR830.instrument import QSR830


class QSR830Widget(QInstrumentWidget):
    '''Stanford Research Systems SR830 Lock-in Amplifier
    '''

    UIFILE = 'SR830Widget.ui'

    def __init__(self, *args, device=None, **kwargs):
        device = device or QSR830().find()
        super().__init__(*args, device=device, **kwargs)


if __name__ == '__main__':
    QSR830Widget.example()

__all__ = ['QSR830Widget']
