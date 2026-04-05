# QInstrument

[![PyPI version](https://img.shields.io/pypi/v/QInstrument.svg)](https://pypi.org/project/QInstrument/)
[![Tests](https://github.com/davidgrier/QInstrument/actions/workflows/tests.yml/badge.svg)](https://github.com/davidgrier/QInstrument/actions/workflows/tests.yml)
[![Documentation](https://readthedocs.org/projects/qinstrument/badge/?version=latest)](https://qinstrument.readthedocs.io/en/latest/)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.19424797.svg)](https://doi.org/10.5281/zenodo.19424797)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

A Qt-based framework for controlling scientific instruments over serial ports.
Instruments are represented as Qt objects with a uniform property system,
automatic UI binding, and JSON-based configuration persistence.
Any Qt binding (PyQt5, PyQt6, PySide2, PySide6) is supported via `qtpy`.

## Instruments

### IPG Photonics
- **YLR Series**: Ytterbium fiber laser

### Laser Quantum
- **Opus**: Continuous-wave laser

### PiezoDrive
- **PDUS210**: Piezo transducer driver

### Prior Scientific
- **Proscan II/III**: Motorized microscope stage controller

### Stanford Research Systems
- **DS345**: 30 MHz Synthesized Function Generator
- **SR830**: 100 kHz Digital Lock-in Amplifier
- **SR844**: 200 MHz RF Lock-in Amplifier

### Tektronix
- **TDS1000**: Digital oscilloscope

## Installation

```bash
pip install QInstrument
pip install PyQt6          # or PyQt5, PySide2, PySide6
```

Installing from PyPI also places a `qinstrument` command on your PATH.

To install from source:

```bash
git clone https://github.com/davidgrier/QInstrument
cd QInstrument
python -m venv .qi
source .qi/bin/activate
pip install -e ".[dev]"
```

## Quick start

### Rack application

Launch the rack to control multiple instruments at once:

```bash
qinstrument DS345 SR830
```

On subsequent runs, `qinstrument` with no arguments restores the
last-used instrument list automatically.  Use the **Add instrument…**
button to add instruments at runtime, or right-click any instrument
to remove it.

<img src="https://raw.githubusercontent.com/davidgrier/QInstrument/main/docs/QDS345Widget.png" width="50%" alt="DS345 Widget">

### Single instrument widget

Each instrument widget also has a built-in `example()` entry point:

```bash
python -m QInstrument.instruments.DS345.widget
```

This finds a connected DS345 and opens its control panel.
If no instrument is detected it falls back automatically to a
simulated (fake) device so the UI is always usable.

### Embedding a widget in your application

```python
from qtpy.QtWidgets import QApplication
from QInstrument.instruments.DS345 import QDS345Widget

app = QApplication([])
widget = QDS345Widget()
widget.show()
app.exec()
```

### Using a simulated instrument

When hardware is not available, pass a fake device directly:

```python
from QInstrument.instruments.DS345 import QDS345Widget, QFakeDS345

app = QApplication([])
widget = QDS345Widget(device=QFakeDS345())
widget.show()
app.exec()
```

## Architecture

```
QtCore.QObject
└── QAbstractInstrument      # property/method registry, thread-safe get/set
    └── QSerialInstrument    # holds QSerialInterface; adds open/find/identify
        └── QXxxInstrument   # concrete instrument

QtSerialPort.QSerialPort
└── QSerialInterface         # raw serial I/O (owned by QSerialInstrument)

QWidget
├── QInstrumentWidget        # loads .ui file; auto-binds widgets to properties;
│                            # saves/restores device state via Configure
└── QInstrumentRack          # holds multiple QInstrumentWidgets; runtime
                             # add/remove; saves/restores instrument list
```

Each instrument lives in `instruments/<Name>/` with three files:

| File | Purpose |
|------|---------|
| `instrument.py` | Serial communication and property registration |
| `fake.py` | Simulated instrument for UI development without hardware |
| `widget.py` | Qt widget, `.ui` file binding, `example()` entry point |

## Development

Run the test suite:

```bash
source .qi/bin/activate
pytest tests/
```

Tests run automatically before every `git push` via a pre-push hook.
To install the hook in a fresh clone:

```bash
cp hooks/pre-push .git/hooks/pre-push   # if tracked, else set up manually
chmod +x .git/hooks/pre-push
```

## Acknowledgements

Work on this project at New York University is supported by the
National Science Foundation of the United States under award number DMR-2438983.
