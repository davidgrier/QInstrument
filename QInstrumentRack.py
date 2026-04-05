# TODO: Provide methods to search for specific instruments.
# TODO: Provide methods to save and load rack configurations.
# TODO: Provide methods to rearrange instruments in the rack.
# TODO: Provide methods to connect instruments ?
from qtpy import QtWidgets, QtCore
from QInstrument.lib.QInstrumentWidget import QInstrumentWidget
import importlib
from pathlib import Path
import logging


logger = logging.getLogger(__name__)


class QInstrumentRack(QtWidgets.QWidget):
    '''A widget that can hold multiple instrument widgets
    in a vertical layout.

    This class provides methods to add and clear instrument widgets.

    Attributes
    ----------
    description : list[str]
        A list of strings describing the rack or its contents. This can
        be used for documentation or display purposes.
    '''

    def __init__(self,
                 parent: QtWidgets.QWidget | None = None,
                 description: list[str] | None = None) -> None:
        super().__init__(parent)
        self._setupUi()
        self.addInstrumentsByNames(description)

    def _setupUi(self) -> None:
        self.setLayout(QtWidgets.QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(0)

    def addInstrument(self,
                      instrument_widget: QInstrumentWidget) -> None:
        '''Add an instrument widget to the rack.

        This method takes an instance of QInstrumentWidget and adds it
        to the vertical layout of the rack.

        Parameters
        ----------
        instrument_widget : QInstrumentWidget
            The instrument widget to be added to the rack.
        '''
        self.layout().addWidget(instrument_widget)

    def addInstruments(self,
                       instruments: list[QInstrumentWidget]) -> None:
        '''Add multiple instrument widgets to the rack.

        This method takes a list of QInstrumentWidget instances and adds
        them to the vertical layout of the rack.

        Parameters
        ----------
        instruments : list[QInstrumentWidget]
            A list of instrument widgets to be added to the rack.

        '''
        for instrument in instruments:
            self.addInstrument(instrument)

    def addInstrumentByName(self, name: str) -> None:
        '''Add an instrument widget by its class name.

        This method assumes that the instrument widget class is defined
        in a module with the same name as the class, located in the
        "instruments" directory.

        Parameters
        ----------
        name : str
            The name of the instrument widget class to be added
                (without the "Q" prefix and "Widget" suffix).
        '''
        modulename = f'QInstrument.instruments.{name}.widget'
        widgetname = f'Q{name}Widget'
        try:
            mod = importlib.import_module(modulename)
            cls = getattr(mod, widgetname)
            instrument = cls()
        except (ModuleNotFoundError, AttributeError) as e:
            logger.warning(f"Error loading instrument '{name}': {e}")
            return
        self.addInstrument(instrument)

    def addInstrumentsByNames(self, names: list[str]) -> None:
        '''Add multiple instrument widgets by their class names.

        This method takes a list of instrument names and adds the
        corresponding instrument widgets to the rack using the
        addInstrumentByName method.

        Parameters
        ----------
        names : list[str]
            A list of instrument widget class names to be added
                (without the "Q" prefix and "Widget" suffix).
        '''
        for name in names:
            self.addInstrumentByName(name)

    def clearInstruments(self) -> None:
        while self.layout().count():
            child = self.layout().takeAt(0)
            if child.widget():
                child.widget().deleteLater()


def example() -> None:
    app = QtWidgets.QApplication([])
    rack = QInstrumentRack(description='Proscan DS345 SR830'.split())
    rack.show()
    app.exec()


if __name__ == "__main__":
    example()
