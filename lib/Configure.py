from qtpy import QtCore, QtWidgets
from pathlib import Path
import json
from datetime import datetime
import logging


logger = logging.getLogger(__name__)


class Configure(QtCore.QObject):
    '''Save and restore configuration of objects

    The configuration object also includes utility functions for
    standard timestamps and standard file names

    Methods
    -------
    timestamp() : str
        Returns a string representation of the current time.
    filename([prefix], [suffix]) : str
        Returns a string intended for use as a filename.
    configname(object) : str
        Returns the filename for a configuration file.
    save(object) :
        Save the configuration of a specified object.
    restore(object) :
        Read configuration and set properties of object.
    '''

    def __init__(self,
                 datadir: str | None = None,
                 configdir: str | None = None) -> None:
        super().__init__()
        self.datadir = Path(datadir or '~/data/').expanduser()
        self.configdir = Path(configdir or '~/.QInstrument/').expanduser()
        if not self.datadir.exists():
            logger.info(f'Creating data directory: {self.datadir}')
            self.datadir.mkdir(parents=True)
        if not self.configdir.exists():
            logger.info(
                f'Creating configuration directory: {self.configdir}')
            self.configdir.mkdir(parents=True)

    def timestamp(self) -> str:
        '''Returns string representing the current date and time'''
        return datetime.now().strftime('_%Y%b%d_%H%M%S')

    def filename(self,
                 prefix: str = 'QInstrument',
                 suffix: str = '') -> str:
        '''Returns a file name, including timestamp

        Arguments
        ---------
        prefix : str
            String prefix for the filename.
            Default: QInstrument
        suffix : str
            String suffix to append to filename.
            Default: ''
        '''
        name = prefix + self.timestamp() + suffix
        return str(self.datadir / name)

    def configname(self, obj: object) -> str:
        '''Returns name of configuration file based on class of objects

        Parameters
        ----------
        obj : object
            Configuration file is named based on class name of objects

        Returns
        -------
        configname : str
            File name for configuration file
        '''
        classname = obj.__class__.__name__
        return str(self.configdir / (classname + '.json'))

    def save(self, obj: object) -> None:
        '''Save configuration of object as json file

        Parameters
        ----------
        object : object
            Object must have settings property, which provides
            a dictionary of parameters to be saved.
        '''
        settings = obj.settings
        if len(settings) == 0:
            return
        filename = self.configname(obj)
        with open(filename, 'w', encoding='utf-8') as configfile:
            json.dump(settings, configfile,
                      indent=2, separators=(',', ': '),
                      ensure_ascii=False)

    def restore(self, obj: object) -> None:
        '''Restore object configuration from json file

        Parameters
        ----------
        object : object
            Reads configuration for object from a configuration file
            based on the object class name
        '''
        try:
            filename = self.configname(obj)
            logger.info(f'Configuring {filename}')
            with open(filename, 'r', encoding='utf-8') as configfile:
                obj.settings = json.load(configfile)
        except Exception as ex:
            logger.warning(
                f'Could not read {filename}: {ex}'
                '\n\tUsing default configuration.')

    def query_save(self, obj: object) -> None:
        mbox = QtWidgets.QMessageBox
        msg = mbox(self.parent)
        msg.setWindowTitle('Confirmation')
        msg.setText('Save current configuration?')
        msg.setStandardButtons(mbox.StandardButton.Yes |
                               mbox.StandardButton.No)
        response = msg.exec()
        if response = mbox.StandardButton.Yes:
            self.save(obj)
