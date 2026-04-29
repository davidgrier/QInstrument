from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path

from qtpy import QtCore, QtWidgets


logger = logging.getLogger(__name__)


class Configure(QtCore.QObject):
    '''Save and restore instrument configuration to and from JSON files.

    Configuration files are named after the class of the target object
    and stored under :attr:`configdir`.  Timestamped data filenames are
    generated under :attr:`datadir`.

    Parameters
    ----------
    datadir : str | None
        Directory for timestamped data files.
        Default: ``~/data/``.
    configdir : str | None
        Directory for JSON configuration files.
        Default: ``~/.QInstrument/``.

    Attributes
    ----------
    datadir : Path
        Resolved path to the data directory.
    configdir : Path
        Resolved path to the configuration directory.
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
            logger.info(f'Creating configuration directory: {self.configdir}')
            self.configdir.mkdir(parents=True)

    def timestamp(self) -> str:
        '''Return a string representing the current date and time.

        Returns
        -------
        str
            Timestamp formatted as ``_YYYYMonDD_HHMMSS``
            (e.g. ``_2024Jan15_143022``).
        '''
        return datetime.now().strftime('_%Y%b%d_%H%M%S')

    def filename(self,
                 prefix: str = 'QInstrument',
                 suffix: str = '') -> str:
        '''Return a timestamped filename under :attr:`datadir`.

        Parameters
        ----------
        prefix : str
            String prepended to the filename. Default: ``'QInstrument'``.
        suffix : str
            String appended after the timestamp. Default: ``''``.

        Returns
        -------
        str
            Absolute path string of the form
            ``<datadir>/<prefix><timestamp><suffix>``.
        '''
        return str(self.datadir / (prefix + self.timestamp() + suffix))

    def configname(self, obj: object) -> str:
        '''Return the path to the JSON configuration file for *obj*.

        The filename is derived from ``obj``'s class name, so all
        instances of the same class share one configuration file.

        Parameters
        ----------
        obj : object
            Object whose class name determines the configuration filename.

        Returns
        -------
        str
            Absolute path string of the form
            ``<configdir>/<ClassName>.json``.
        '''
        return str(self.configdir / (obj.__class__.__name__ + '.json'))

    def save(self, obj: object,
             settings: dict | None = None) -> None:
        '''Save *obj*'s settings to its JSON configuration file.

        Reads ``obj.settings`` (a dict) and serializes it to
        :meth:`configname`.  Does nothing when the settings dict is empty.
        An explicit *settings* dict may be supplied to avoid reading from
        *obj* directly — useful when *obj* lives in a worker thread.

        Parameters
        ----------
        obj : object
            Object whose class name determines the configuration filename.
        settings : dict or None, optional
            Settings to save.  When ``None`` (default), reads
            ``obj.settings``.
        '''
        settings = obj.settings if settings is None else settings
        if not settings:
            return
        filename = self.configname(obj)
        with open(filename, 'w', encoding='utf-8') as configfile:
            json.dump(settings, configfile,
                      indent=2, separators=(',', ': '),
                      ensure_ascii=False)

    def restore(self, obj: object) -> None:
        '''Restore *obj*'s settings from its JSON configuration file.

        Reads the JSON file at :meth:`configname` and assigns the result
        to ``obj.settings``.  Logs a warning and leaves *obj* unchanged
        if the file does not exist or cannot be parsed.

        Parameters
        ----------
        obj : object
            Object with a ``settings`` property whose setter accepts a
            ``dict[str, bool | int | float | str]``.
        '''
        filename = self.configname(obj)
        try:
            logger.info(f'Configuring {filename}')
            with open(filename, 'r', encoding='utf-8') as configfile:
                obj.settings = json.load(configfile)
        except Exception as ex:
            logger.warning(
                f'Could not read {filename}: {ex}'
                '\n\tUsing default configuration.')

    def read(self, obj: object) -> dict | None:
        '''Read and return *obj*'s saved configuration without applying it.

        Reads the JSON file at :meth:`configname` and returns its
        contents as a dict.  Returns ``None`` if the file does not
        exist or cannot be parsed, without logging a warning.

        Parameters
        ----------
        obj : object
            Object whose class name determines the configuration filename.

        Returns
        -------
        dict or None
            Saved configuration dict, or ``None`` if unavailable.
        '''
        filename = self.configname(obj)
        try:
            with open(filename, 'r', encoding='utf-8') as configfile:
                return json.load(configfile)
        except Exception:
            return None

    def query_save(self, obj: object) -> None:
        '''Prompt the user and save *obj*'s settings if confirmed.

        Opens a modal dialog asking whether to save the current
        configuration.  Calls :meth:`save` if the user clicks Yes.

        Parameters
        ----------
        obj : object
            Object to save if the user confirms.
        '''
        mbox = QtWidgets.QMessageBox
        msg = mbox(self.parent())
        msg.setWindowTitle('Confirmation')
        msg.setText('Save current configuration?')
        msg.setStandardButtons(mbox.StandardButton.Yes |
                               mbox.StandardButton.No)
        if msg.exec() == mbox.StandardButton.Yes:
            self.save(obj)


__all__ = ['Configure']
