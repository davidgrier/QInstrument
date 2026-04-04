# QInstrument

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

A Qt-based framework for controlling scientific instruments over serial ports.
Instruments are represented as Qt objects with a uniform property system,
automatic UI binding, and JSON-based configuration persistence.
Any Qt binding (PyQt5, PyQt6, PySide2, PySide6) is supported via `qtpy`.

## Instruments

### IPG Photonics
- **YLR Series**: Ytterbium fibre laser

### Laser Quantum
- **Opus**: Continuous-wave laser

### PiezoDrive
- **PDUS210**: Piezo transducer driver

### Prior Scientific
- **Proscan II/III**: Motorised microscope stage controller

### Stanford Research Systems
- **DS345**: 30 MHz Synthesised Function Generator
- **SR830**: 100 kHz Digital Lock-in Amplifier
- **SR844**: 200 MHz RF Lock-in Amplifier

### Tektronix
- **TDS1000**: Digital oscilloscope

## Installation

```bash
git clone https://github.com/davidgrier/QInstrument
cd QInstrument
python -m venv .qi
source .qi/bin/activate
pip install -r requirements.txt
```

## Quick start

Each instrument widget has a built-in `example()` entry point.
Run it directly from the command line:

```bash
python -m QInstrument.instruments.DS345.widget
```

This finds a connected DS345 and opens its control panel.
If no instrument is detected it falls back automatically to a simulated
(fake) device so the UI is always usable.

You can also drive the widget from your own application:

```python
from qtpy.QtWidgets import QApplication
from QInstrument.instruments.DS345 import QDS345Widget

app = QApplication([])
widget = QDS345Widget()
widget.show()
app.exec()
```

<img src="https://raw.githubusercontent.com/davidgrier/QInstrument/main/docs/QDS345Widget.png" width="50%" alt="DS345 Widget">

### Using a simulated instrument

When hardware is not available, import the fake class directly:

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
└── QAbstractInstrument      # property/method registry, thread-safe get/set, settings I/O
    └── QSerialInstrument    # holds QSerialInterface; adds open/find/identify
        └── QXxxInstrument   # concrete instrument

QtSerialPort.QSerialPort
└── QSerialInterface         # raw serial I/O (owned by QSerialInstrument)

QWidget
└── QInstrumentWidget        # loads .ui file, auto-binds widgets to registered properties
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
