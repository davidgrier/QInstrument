import logging
from .QAbstractInstrument import QAbstractInstrument

logger = logging.getLogger(__name__)


class QFakeInstrument(QAbstractInstrument):
    '''Base class for fake instruments used in UI development without hardware.

    Inherits :class:`QAbstractInstrument` to provide the full
    ``registerProperty()`` API.  Subclasses call ``registerProperty()``
    in ``__init__`` for each property, mirroring the real instrument
    they simulate.
    '''

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.identification = 'Fake Instrument'

    def busy(self) -> bool:
        return False

    def isOpen(self) -> bool:
        return True
