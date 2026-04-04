from QInstrument.lib.QInstrumentWidget import QInstrumentWidget
from QInstrument.instruments.DS345.instrument import QDS345


class QDS345Widget(QInstrumentWidget):
    '''Stanford Research Systems DS345 Function Generator
    '''

    UIFILE = 'DS345Widget.ui'

    def __init__(self, *args, device=None, **kwargs):
        device = device or QDS345().find()
        super().__init__(*args, device=device, **kwargs)


if __name__ == '__main__':
    QDS345Widget.example()

__all__ = ['QDS345Widget']
