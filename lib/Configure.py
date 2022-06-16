from PyQt5.QtCore import QObject
from PyQt5.QtWidgets import QMessageBox
import json
import os
import io
from datetime import datetime

import logging

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)


class Configure(QObject):
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

    def __init__(self, *args,
                 datadir=None,
                 configdir=None,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self.datadir = os.path.expanduser(datadir or '~/data/')
        self.configdir = os.path.expanduser(configdir or '~/.QInstrument/')
        if not os.path.exists(self.datadir):
            logger.info(f'Creating data directory: {self.datadir}')
            os.makedirs(self.datadir)
        if not os.path.exists(self.configdir):
            logger.info(
                f'Creating configuration directory: {self.configdir}')
            os.makedirs(self.configdir)

    def timestamp(self):
        '''Returns string representing the current date and time'''
        return datetime.now().strftime('_%Y%b%d_%H%M%S')

    def filename(self, prefix=None, suffix=None):
        '''Returns a file name, including timestamp

        Arguments
        ---------
        prefix : str, optional
            String prefix for the filename.
            Default: QInstrument
        suffix : str, optional
            String suffix to append to filename.
            Default: None
        '''
        name = prefix or 'QInstrument'
        name += self.timestamp() + suffix
        return os.path.join(self.datadir, name)

    def configname(self, object):
        '''Returns name of configuration file based on class of objects

        Parameters
        ----------
        object : object
            Configuration file is named based on class name of objects

        Returns
        -------
        configname : str
            File name for configuration file

        '''
        classname = object.__class__.__name__
        return os.path.join(self.configdir, classname + '.json')

    def save(self, object):
        '''Save configuration of object as json file

        Parameters
        ----------
        object : object
            Object must have settings property, which provides
            a dictionary of parameters to be saved.
        '''
        settings = object.settings
        if len(settings) == 0:
            return
        configuration = json.dumps(settings,
                                   indent=2,
                                   separators=(',', ': '),
                                   ensure_ascii=False)
        filename = self.configname(object)
        with io.open(filename, 'w', encoding='utf8') as configfile:
            configfile.write(configuration)
#            if platform.python_version().startswith('3.'):
#                configfile.write(str(configuration))
#            else:
#                configfile.write(unicode(configuration))

    def restore(self, object):
        '''Restore object configuration from json file

        Parameters
        ----------
        object : object
            Reads configuration for object from a configuration file
            based on the object class name
        '''
        try:
            filename = self.configname(object)
            logger.info(f'Configuring {filename}')
            configuration = json.load(io.open(filename))
            object.settings = configuration
        except IOError as ex:
            msg = (f'Could not read {filename}: {ex}'
                   '\n\tUsing default configuration.')
            logger.warning(msg)

    def query_save(self, object):
        query = 'Save current configuration?'
        reply = QMessageBox.question(self.parent,
                                     'Confirmation',
                                     query,
                                     QMessageBox.Yes,
                                     QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.save(object)
        else:
            pass
