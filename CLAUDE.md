# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

QInstrument is a framework for controlling scientific instruments over serial ports. It provides a property registration system, automatic UI binding, and JSON-based configuration persistence. It targets any installed Qt binding (PyQt5, PyQt6, PySide2, PySide6) via `qtpy`.

Active development happens on the `devel` branch. The `lib/` foundations are fully migrated to the current design. Instrument classes are being migrated one by one; `instruments/DS345/` is the archetype for that work.

## Development Commands

The virtual environment lives in `.qi/` (not `venv/`):
```bash
source .qi/bin/activate
pip install -r requirements.txt
```

Run a specific instrument widget interactively:
```bash
python -c "from qtpy.QtWidgets import QApplication; import sys; from instruments.DS345 import QDS345Widget; app = QApplication(sys.argv); w = QDS345Widget(); w.show(); sys.exit(app.exec())"
```

Tests cover `QSerialInterface` only; run with `pytest tests/`. No build step or linter configuration.

## Architecture

### Core Class Hierarchy

```
QtCore.QObject
└── QAbstractInstrument          # Property/method registration, thread-safe access
    └── QSerialInstrument        # Holds QSerialInterface by composition; adds find/open
        └── QXXXInstrument       # Concrete instrument (e.g. QDS345, QIPGLaser)

QtSerialPort.QSerialPort
└── QSerialInterface             # Raw serial I/O (owned by QSerialInstrument, not inherited)

QWidget
└── QInstrumentWidget            # Auto-binds Qt UI widgets to instrument properties
```

Instruments *possess* an interface rather than *being* one. `QSerialInstrument` holds a `QSerialInterface` as `self._interface` and delegates `transmit()`/`receive()` through it. This means the same instrument class can be used with different transports (e.g. RS-232 and GPIB) by swapping out the interface object.

### Key Abstractions

**`lib/QAbstractInstrument.py`** — Base for all instruments. Properties are explicitly registered via `registerProperty(name, getter, setter, ptype, **meta)`. Provides `get(key)`/`set(key, value)` Qt slots, `settings` dict, and `propertyValue(str, object)` signal (emitted by both `get` and `set`). Uses `QMutex` to protect the property registry; the lock is released before calling any getter/setter/method so that callables may safely re-enter the API without deadlocking.

**`lib/QSerialInterface.py`** — Wraps `QSerialPort`. Provides `transmit(data)`, `receive(eol, raw)`, `open(portName)`, and blocking/non-blocking I/O via the `blocking` property. Does **not** perform device identification — that is the instrument's responsibility.

**`lib/QSerialInstrument.py`** — Inherits `QAbstractInstrument`. Creates and holds a `QSerialInterface` in `__init__`. Implements `transmit()`/`receive()` by delegation, provides `open()` (with `identify()` check), `find()` (port scanning), `isOpen()`, and `close()`. Re-exports the `QSerialPort` enum types (`BaudRate`, `DataBits`, etc.) as class attributes so subclass `comm` dicts need no extra imports. This is what concrete instruments inherit from.

**`lib/QInstrumentWidget.py`** — Loads a `.ui` file and auto-links named widgets to instrument properties by matching widget names to registered property names. Uses `device.get(key)` and `device.set(key, value)` (the Qt slots on `QAbstractInstrument`) — not `getattr`/`setattr`, which do not work with `registerProperty()`-based instruments. Calls `_identifyProperties()` / `_syncProperties()` / `_connectSignals()` automatically.

**`lib/Configure.py`** — Saves/restores `object.settings` as JSON to `~/.QInstrument/<ClassName>.json`. Also provides timestamped data filenames under `~/data/`.

**`lib/QFakeInstrument.py`** — Mock instrument base for UI development without hardware.

### Adding a New Instrument

Each instrument lives in `instruments/<Name>/` and follows this pattern:

1. **`instrument.py`** — Inherits `QSerialInstrument`. Define a `comm` class attribute with serial parameters. In `__init__`, call `super().__init__(portName, **kwargs)` then `_registerProperties()` and `_registerMethods()`. Implement `identify()` to verify the connected device.
2. **`fake.py`** — Inherits `QFakeInstrument`. Mirrors the same properties for UI testing without hardware.
3. **`widget.py`** — Inherits `QInstrumentWidget`. Points to a `.ui` file; widget names must match registered property names for auto-binding to work. Set `FAKEDEVICE` to the fake class so `example()` can fall back to it.
4. **`__init__.py`** — Exports the main classes by name: `from .instrument import QName`, etc.

See `instruments/DS345/` for the reference implementation.

### Qt Imports

**Always import Qt via `qtpy`**, not directly from PyQt5/PyQt6 and not via `pyqtgraph.Qt`:
```python
from qtpy import QtCore, QtWidgets
from qtpy.QtSerialPort import QSerialPort, QSerialPortInfo
```
Use `QtCore.Signal`, `QtCore.Slot`, and `QtCore.Property` — **not** `pyqtSignal`, `pyqtSlot`, or `pyqtProperty`, which are PyQt5-specific names unavailable through `qtpy`.

### Property System

**All instrument properties use `registerProperty()`** — never `pyqtProperty`. This is a firm design decision.

`registerProperty()` is called in `__init__` rather than declared as class attributes because some instruments only discover their properties at runtime (after `identify()` runs). It also stores UI metadata (`minimum`, `maximum`, `step`) and emits the uniform `propertyValue(str, object)` signal without per-property boilerplate.

`QFakeInstrument` must also use `registerProperty()`. Fake instruments mirror real instruments: register the same properties in `__init__`, using the `_AUTO` backing-attribute convention or explicit callables. Read-only properties pass `setter=None`.

Existing instruments in `instruments/` that predate this decision still use `pyqtProperty`. They must be migrated; do not add any new `pyqtProperty` usage anywhere in the codebase.

#### `_register()` helper

Instruments whose properties follow the standard DS345-style command convention (`CMD?` to query, `CMDvalue` to set) should define a `_register(name, cmd, dtype=float)` helper in `__init__` to eliminate per-property boilerplate:

```python
def _register(self, name: str, cmd: str, dtype: type = float) -> None:
    if dtype is bool:
        def getter(): return bool(self.getValue(f'{cmd}?', int))
        def setter(v): return self.transmit(f'{cmd}{int(bool(v))}')
    else:
        def getter(): return self.getValue(f'{cmd}?', dtype)
        def setter(v): return self.transmit(f'{cmd}{dtype(v)}')
    self.registerProperty(name, getter=getter, setter=setter, ptype=dtype)
```

Properties that don't fit the pattern (non-standard response format, internal state) use `registerProperty()` directly.

### Transport Layer Contract

`QAbstractInstrument` provides `handshake(cmd)`, `getValue(cmd, dtype)`, and `expect(cmd, response)` as transport-agnostic helpers. They delegate to `transmit()` and `receive()`, which must be supplied by the transport layer (e.g. `QSerialInterface`). These helpers belong in `QAbstractInstrument`, not in the transport layer, because they are needed by every instrument regardless of communication medium (serial, GPIB, etc.).

When an instrument method needs to read one of its own registered properties, use `self.get('propname')` rather than calling the wire protocol directly. This keeps methods decoupled from protocol details. `get()` returns `PropertyValue | None`; assert the result is not None when the property is guaranteed to be registered.

## Coding Conventions

### Serial enum constants

**Define `comm` as a class attribute** using long-form scoped enum access via `QSerialInstrument`:
```python
comm = dict(baudRate=QSerialInstrument.BaudRate.Baud9600,
            dataBits=QSerialInstrument.DataBits.Data8,
            stopBits=QSerialInstrument.StopBits.OneStop,
            parity=QSerialInstrument.Parity.NoParity,
            flowControl=QSerialInstrument.FlowControl.NoFlowControl,
            eol='\n')

def __init__(self, portName=None, **kwargs):
    super().__init__(portName, **(self.comm | kwargs))
```
`QSerialInstrument` exposes `BaudRate`, `DataBits`, `StopBits`, `Parity`, and `FlowControl` as explicit class attributes (defined in `QSerialInterface`) so they are accessible at class-body evaluation time. Do **not** use short-form access (`QSerialInstrument.Baud9600` etc.) — short-form fails with PyQt6, which dropped it entirely. No `QSerialPort` import is needed in instrument files.

### Imports from `lib/`

`lib/__init__.py` is empty. Always import classes by their full module path:
```python
from QInstrument.lib.QSerialInstrument import QSerialInstrument
from QInstrument.lib.QInstrumentWidget import QInstrumentWidget
from QInstrument.lib.QFakeInstrument import QFakeInstrument
```
`from QInstrument.lib import QSerialInstrument` imports the *module*, not the class, and will fail when used as a base class.

### Instance variable initialisation

Don't initialize instance variables that are always written before they are read. Use a bare annotation instead:
```python
self._saved_amplitude: float   # set on mute, restored on unmute
```
Only provide a default when it is genuinely meaningful.

### Method naming

Method names must match what the method does. When writing or reviewing a docstring, verify that the DS345 (or other instrument) command mnemonic matches the method name. Rename if they conflict.

### Docstrings

- **Class docstring**: no `Inherits` section (redundant with the class signature); units in the property name line as `[unit]`; ranges on their own line; enumerate all int enum values.
- **Method docstrings**: use `Parameters` (not `Arguments`); state preconditions and side effects; document idempotency where relevant.
- `identify()` always gets a docstring explaining what response it checks for.

### Type hints

Add type hints to all new and migrated instrument code. Use `str | None` union syntax (Python 3.10+). Use `numpy.typing.ArrayLike` for array parameters.

## Migration Status

### Completed

- `lib/` — fully migrated: `qtpy` throughout, `registerProperty()` API, `QInstrumentWidget` uses `device.get()`/`device.set()`
- `instruments/DS345/` — reference implementation: `_register()` helper, type hints, full docstrings
- `instruments/SR830/` — fully migrated: MRO fake, `auto_offset_x/y/r` wrappers, full docstrings
- `instruments/SR844/` — fully migrated: MRO fake, `auto_offset_x/y/r` wrappers, full docstrings; legacy `Q*.py` files removed
- `instruments/IPGLaser/` — fully migrated: `_registerProperties()`, MRO fake with explicit `_store` getters (no `_register()` helper — properties derive from a hardware status bitfield), `status()` batch method, efficient `_poll`, `fault_detail()`; legacy `Ipglaser.py` removed
- All `comm` dicts across all instruments — updated to long-form enum access

- `instruments/Opus/` — fully migrated: `_registerProperties()`, IPGLaser-pattern fake with explicit `_store` getters, synchronous timer poll replacing broken async `dataReady` approach, `timers()` using `receive()` loop; `fake.py` added
- `instruments/Proscan/` — fully migrated: `_registerProperties()` with explicit lambdas (no `_register()` helper — Proscan uses comma-delimited `CMD,value` protocol, not DS345-style `CMD?`/`CMDvalue`), IPGLaser-pattern fake with `_store` getters, synchronous `QTimer` poll, `_connectSignals()` for joystick/zdial/buttons; `fake.py` added; `dataReady` async pattern replaced
- `instruments/PiezoDrive/` — fully migrated: `_registerProperties()` with explicit lambdas, three property groups (setpoints, gain, toggle/bool, measured/read-only), `state()` bulk binary read via `self._interface.readn(80)`, `_toggle()` helper for asymmetric enable/disable commands, IPGLaser-pattern fake with `_store` getters; `fake.py` added

### In Development

- `instruments/TDS1000/` — experimental; supports waveform data acquisition only (no property-based control, no widget, no fake). Not subject to migration requirements until the scope is defined.
