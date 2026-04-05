'''Entry point for the QInstrument rack application.

Run as:
    python -m QInstrument [INSTRUMENT ...]
    qinstrument [INSTRUMENT ...]

If no instrument names are given, the previously saved rack
configuration is restored from
``~/.QInstrument/QInstrumentRack.json``.
'''
import sys
import argparse

from qtpy.QtWidgets import QApplication
from QInstrument.QInstrumentRack import QInstrumentRack


def main() -> None:
    '''Launch the QInstrument rack application.'''
    parser = argparse.ArgumentParser(
        prog='qinstrument',
        description='QInstrument rack controller',
    )
    parser.add_argument(
        'instruments', nargs='*',
        metavar='INSTRUMENT',
        help='instrument names to load (e.g. DS345 SR830)',
    )
    args = parser.parse_args()
    app = QApplication.instance() or QApplication(sys.argv)
    rack = QInstrumentRack(
        instruments=args.instruments or None,
    )
    rack.setWindowTitle('QInstrument')
    rack.setMinimumWidth(400)
    rack.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
