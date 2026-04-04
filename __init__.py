from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version('QInstrument')
except PackageNotFoundError:
    # Package is not installed (e.g. running directly from the source tree)
    __version__ = None
