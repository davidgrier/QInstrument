# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

QInstrument is a framework for controlling scientific instruments over serial ports. It provides a property registration system, automatic UI binding, and JSON-based configuration persistence. It targets any installed Qt binding (PyQt5, PyQt6, PySide2, PySide6) via `pyqtgraph.Qt`.

Active development happens on the `devel` branch. The `lib/` foundations are being revised before instrument classes are migrated.

## Development Commands

The virtual environment lives in `.qi/` (not `venv/`):
```bash
source .qi/bin/activate
pip install -r requirements.txt
```

Run a specific instrument widget interactively:
```bash
python -c "from PyQt5.QtWidgets import QApplication; import sys; from instruments.DS345 import QDS345Widget; app = QApplication(sys.argv); w = QDS345Widget(); w.show(); sys.exit(app.exec_())"
```

Tests cover `QSerialInterface` only; run with `pytest tests/`. No build step or linter configuration.

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

**`lib/QInstrumentMixin.py`** — Base for all instruments. Properties are explicitly registered via `registerProperty(name, getter, setter, ptype, **meta)`. Provides `get(key)`/`set(key, value)` Qt slots, `settings` dict, and `propertyValue(str, object)` signal (emitted by both `get` and `set`). Uses `QMutex` to protect the property registry; the lock is released before calling any getter/setter/method so that callables may safely re-enter the API without deadlocking.

**`lib/QSerialInterface.py`** — Wraps `QSerialPort`. Key methods: `find(**kwargs)` (auto-detect device by scanning ports), `transmit(data)`, `receive(eol, raw)`. Supports blocking and non-blocking I/O via `blocking` property.

**`lib/QSerialInstrument.py`** — Thin multiple-inheritance combiner of `QInstrumentMixin` and `QSerialInterface`. This is what concrete instruments inherit from.

**`lib/QInstrumentWidget.py`** — Loads a `.ui` file and auto-links named widgets to instrument properties by matching widget names to registered property names. Calls `_identifyProperties()` / `_syncProperties()` / `_connectSignals()` automatically.

**`lib/Configure.py`** — Saves/restores `object.settings` as JSON to `~/.QInstrument/<ClassName>.json`. Also provides timestamped data filenames under `~/data/`.

**`lib/QFakeInstrument.py`** — Mock instrument base for UI development without hardware.

### Adding a New Instrument

Each instrument lives in `instruments/<Name>/` and follows this pattern:

1. **`QName.py`** — Inherits `QSerialInstrument`. In `__init__`, set serial params (`baudrate`, `eol`, etc.) and call `registerProperty(...)` for each controllable parameter. Implement `identify()` to verify the connected device.
2. **`QFakeName.py`** — Inherits `QFakeInstrument`. Mirrors the same properties for UI testing without hardware.
3. **`QNameWidget.py`** — Inherits `QInstrumentWidget`. Points to a `.ui` file; widget names must match registered property names for auto-binding to work.
4. **`__init__.py`** — Exports the main classes.

### Qt Imports

**Always import Qt via `pyqtgraph.Qt`**, not directly from PyQt5/PyQt6:
```python
from pyqtgraph.Qt import QtCore, QtWidgets, QtSerialPort
```
`pyqtgraph.Qt` automatically resolves to whichever Qt binding (PyQt5, PyQt6, PySide2, PySide6) is installed. Do **not** use the try/except PyQt5/PyQt6 import pattern — it is less general and being phased out.

### Property System

Instrument properties are registered via `registerProperty()` at `__init__` time, not declared as `pyqtProperty` class attributes. The `registerProperty()` approach is preferred because some instruments expose properties that are only discoverable at runtime.

Existing instruments in `instruments/` predate this convention and still use `pyqtProperty`. Do not add new `pyqtProperty` usage; they will be migrated to `registerProperty()` once the `lib/` foundations are stable.

### Transport Layer Contract

`QInstrumentMixin` provides `handshake(cmd)`, `getValue(cmd, dtype)`, and `expect(cmd, response)` as transport-agnostic helpers. They delegate to `transmit()` and `receive()`, which must be supplied by the transport layer (e.g. `QSerialInterface`). These helpers belong in `QInstrumentMixin`, not in the transport layer, because they are needed by every instrument regardless of communication medium (serial, GPIB, etc.).
