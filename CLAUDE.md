# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

QInstrument is a PyQt5/PyQt6-compatible framework for controlling scientific instruments over serial ports. It provides a property registration system, automatic UI binding, and JSON-based configuration persistence.

## Development Commands

Install dependencies:
```bash
pip install -r requirements.txt
```

Run a specific instrument widget interactively:
```bash
python -c "from PyQt5.QtWidgets import QApplication; import sys; from instruments.DS345 import QDS345Widget; app = QApplication(sys.argv); w = QDS345Widget(); w.show(); sys.exit(app.exec_())"
```

There is no test suite, build step, or linter configuration.

## Architecture

### Core Class Hierarchy

```
QtCore.QObject
└── QInstrumentMixin          # Property/method registration, thread-safe access
    └── QSerialInstrument     # Inherits QInstrumentMixin + QSerialInterface
        └── QXXXInstrument    # Concrete instrument (e.g., QDS345, QSR830)

QtSerialPort.QSerialPort
└── QSerialInterface          # Serial port I/O, port auto-detection

QWidget
└── QInstrumentWidget         # Auto-binds Qt UI widgets to instrument properties
```

### Key Abstractions

**`lib/QInstrumentMixin.py`** — Base for all instruments. Properties are explicitly registered via `registerProperty(name, getter, setter, ptype, **meta)`. Provides `get(key)`/`set(key, value)` Qt slots, `settings` dict, and `propertyValue` signal. Uses `QMutex` for thread safety.

**`lib/QSerialInterface.py`** — Wraps `QSerialPort`. Key methods: `find(**kwargs)` (auto-detect device by scanning ports), `transmit(data)`, `receive(eol, raw)`. Supports blocking and non-blocking I/O via `blocking` property.

**`lib/QSerialInstrument.py`** — Thin multiple-inheritance combiner of `QInstrumentMixin` and `QSerialInterface`. This is what concrete instruments inherit from.

**`lib/QInstrumentWidget.py`** — Loads a `.ui` file and auto-links named widgets to instrument properties by matching widget names to registered property names. Calls `_identifyProperties()` / `_syncProperties()` / `_connectSignals()` automatically.

**`lib/Configure.py`** — Saves/restores `object.settings` as JSON to `~/.QInstrument/<ClassName>.json`. Also provides timestamped data filenames under `~/data/`.

**`lib/QFakeInstrument.py`** — Mock instrument base for UI development without hardware.

### Adding a New Instrument

Each instrument lives in `instruments/<Name>/` and follows this pattern:

1. **`QName.py`** — Inherits `QSerialInstrument`. In `__init__`, set serial params (`baudrate`, `eol`, etc.) and call `registerProperty(...)` for each controllable parameter. Implement `identify()` to verify the connected device.
2. **`QFakeName.py`** — Inherits `QFakeInstrument`. Mirrors the same properties using the `Property` metaclass pattern for UI testing without hardware.
3. **`QNameWidget.py`** — Inherits `QInstrumentWidget`. Points to a `.ui` file; widget names must match registered property names for auto-binding to work.
4. **`__init__.py`** — Exports the main classes.

### PyQt5 / PyQt6 Compatibility

The codebase targets PyQt5 but is being migrated toward PyQt6 compatibility. `Configure.py` and other files use a try/except import pattern:
```python
try:
    from PyQt5 import ...
except ImportError:
    from PyQt6 import ...
```

Follow this pattern in all new or modified files.
