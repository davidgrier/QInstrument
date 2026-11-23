from typing import TYPE_CHECKING
from QInstrument.lib.QInstrumentWidget import QInstrumentWidget
from QInstrument.instruments.StanfordResearch.SR830.instrument import QSR830


if TYPE_CHECKING:
    from .SR830Widget_ui import UiSR830Widget
else:
    UiSR830Widget = object


class QSR830Widget(QInstrumentWidget, UiSR830Widget):
    '''Stanford Research Systems SR830 Lock-in Amplifier
    '''

    UIFILE = 'SR830Widget.ui'
    INSTRUMENT = QSR830


if __name__ == '__main__':
    QSR830Widget.example()

__all__ = ['QSR830Widget']
