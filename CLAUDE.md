# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

QInstrument is a framework for controlling scientific instruments over serial ports. It provides a property registration system, automatic UI binding, and JSON-based configuration persistence. It targets any installed Qt binding (PyQt5, PyQt6, PySide2, PySide6) via `qtpy`.

All `lib/` foundations and all instrument classes are fully migrated. Instruments are organised under `instruments/<Manufacturer>/<Name>/`; `instruments/StanfordResearch/DS345/` is the reference implementation.

## Development Commands

The virtual environment lives in `.qi/` (not `venv/`):
```bash
source .qi/bin/activate
pip install -e ".[dev]"
```

Run the rack application:
```bash
python -m QInstrument DS345 SR830
```

Run a specific instrument widget interactively:
```bash
python -m QInstrument.instruments.StanfordResearch.DS345.widget
```

Run tests with `pytest tests/`. No build step or linter configuration.

Git hooks live in `.githooks/` (tracked). Activate them once per clone:
```bash
git config core.hooksPath .githooks
```
The `pre-push` hook runs the full test suite and blocks the push on failure.

## Architecture

### Core Class Hierarchy

```
QtCore.QObject
├── QAbstractInstrument          # Property/method registration, thread-safe access
│   └── QSerialInstrument        # Holds QSerialInterface by composition; adds find/open
│       └── QXXXInstrument       # Concrete instrument (e.g. QDS345, QIPGLaser)

QPollingMixin                    # Self-scheduling poll loop; mixed into instruments
                                 # that need continuous updates (e.g. QSR830, QSR844)

QtSerialPort.QSerialPort
└── QSerialInterface             # Raw serial I/O (owned by QSerialInstrument, not inherited)

QWidget
├── QInstrumentWidget            # Auto-binds Qt UI widgets to instrument properties
└── QInstrumentRack              # Holds multiple QInstrumentWidgets; runtime add/remove
```

Instruments *possess* an interface rather than *being* one. `QSerialInstrument` holds a `QSerialInterface` as `self._interface` and delegates `transmit()`/`receive()` through it. This means the same instrument class can be used with different transports (e.g. RS-232 and GPIB) by swapping out the interface object.

### Key Abstractions

**`lib/QAbstractInstrument.py`** — Base for all instruments. Models instrument state as named properties registered via `registerProperty(name, getter, setter, ptype, **meta)`. Provides `get(key)`/`set(key, value)` Qt slots, `settings` dict, and `propertyValue(str, object)` signal (emitted by both `get` and `set`). Uses `QMutex` to protect the property registry; the lock is released before calling any getter/setter/method so that callables may safely re-enter the API without deadlocking. Has no concept of hardware communication — that is the transport layer's responsibility.

**`lib/QPollingMixin.py`** — Mixin that adds a self-scheduling poll loop to any instrument. Mix into a concrete instrument class alongside `QSerialInstrument` to enable continuous property updates. `startPolling()` begins the loop (must be called from the instrument's own thread); call it explicitly after the device has been moved to its worker thread — `QInstrumentWidget` and `QInstrumentTree` do **not** start it automatically. `stopPolling()` sets a flag and is safe from any thread. `POLL_INTERVAL` (default `0`) is the millisecond delay between the end of one response and the start of the next query; `0` gives maximum throughput without query backup. Override `_poll()` to use batched queries; the override must follow the same guard pattern as the default.

**`lib/QSerialInterface.py`** — Wraps `QSerialPort`. Provides `transmit(data)`, `receive(eol, raw)`, `open(portName)`, and blocking I/O. Does **not** perform device identification — that is the instrument's responsibility.

**`lib/QSerialInstrument.py`** — Inherits `QAbstractInstrument`. Extends it with the full serial communication API: `transmit()`, `receive()` (delegated to `QSerialInterface`), and the command-response helpers `handshake()`, `expect()`, and `getValue()`. Also provides `open()` (with `identify()` check), `find()` (port scanning), `isOpen()`, and `close()`. Re-exports the `QSerialPort` enum types (`BaudRate`, `DataBits`, etc.) as class attributes so subclass `comm` dicts need no extra imports. This is what concrete instruments inherit from.

**`lib/QInstrumentWidget.py`** — Loads a `.ui` file and auto-links named widgets to instrument properties by matching widget names to registered property names. Uses `device.get(key)` and `device.set(key, value)` (the Qt slots on `QAbstractInstrument`) — not `getattr`/`setattr`, which do not work with `registerProperty()`-based instruments. Calls `_identifyProperties()` / `_syncProperties()` / `_connectSignals()` automatically. Integrates `Configure`: on first `showEvent` the device's saved settings are restored and the UI re-synced; on `closeEvent` the device settings are saved. Save/restore is gated on `_shown` so test widgets closed during teardown do not write config files. Polling is **not** started automatically; call `startPolling` explicitly (via `QMetaObject.invokeMethod` with `QueuedConnection` so it runs in the worker thread) when continuous updates are needed. `stopPolling` is called in `closeEvent` as a safety net regardless.

**`lib/Configure.py`** — Saves/restores `object.settings` as JSON to `~/.QInstrument/<ClassName>.json`. Also provides timestamped data filenames under `~/data/`. Used directly by `QInstrumentWidget` and `QInstrumentRack`; any object with a `settings` dict property can use it.

**`QInstrumentRack.py`** — Top-level widget that holds multiple `QInstrumentWidget` instances in a vertical layout. Provides an "Add instrument…" toolbar button (opens a picker dialog built from `availableInstruments()`, which scans `instruments/` two levels deep for `<Manufacturer>/<Name>/` subpackages that contain a `widget.py`) and a right-click context menu on each slot for removal. `addInstrumentByName()` resolves a bare instrument name (e.g. `'DS345'`) to its full module path by searching manufacturer subdirectories. Persists the instrument list via `Configure` using the same `_shown`-gated save/restore pattern as `QInstrumentWidget`. `python -m QInstrument [NAME ...]` and the installed `qinstrument` CLI both use this as the entry point; bare invocation restores the last session.

**`lib/QFakeInstrument.py`** — Mock instrument base for UI development without hardware.

### Adding a New Instrument

Instruments are organised under `instruments/<Manufacturer>/<Name>/`.
If the manufacturer directory does not yet exist, create it with an
empty `__init__.py` and add it to the `packages` list in
`pyproject.toml`.

Each instrument package follows this pattern:

1. **`instrument.py`** — Inherits `QSerialInstrument`. Define a `comm` class attribute with serial parameters. In `__init__`, call `super().__init__(portName, **kwargs)` — `_registerProperties()` and `_registerMethods()` are called automatically by `QAbstractInstrument.__init__` and must **not** be called explicitly. Implement `identify()` to verify the connected device.
2. **`fake.py`** — Inherits `QFakeInstrument`. Mirrors the same properties for UI testing without hardware.
3. **`widget.py`** — Inherits `QInstrumentWidget`. Points to a `.ui` file; widget names must match registered property names for auto-binding to work. Set `FAKEDEVICE` to the fake class so `example()` can fall back to it.
4. **`tree.py`** — Inherits `QInstrumentTree`. Declares `INSTRUMENT = QName`. No other code required.
5. **`__init__.py`** — Lazy-loads the main classes: `QName`, `QFakeName`, `QNameWidget`.
6. **`pyproject.toml`** — Add `"QInstrument.instruments.<Manufacturer>.<Name>"` to the `packages` list.

See `instruments/StanfordResearch/DS345/` for the reference implementation.

When an instrument family shares a communication protocol but differs
only in hardware constants (power limits, wavelength, etc.), define a
base class in `instruments/<Manufacturer>/<Family>/instrument.py` and
place model-specific constants as class attributes on thin subclasses
in `instruments/<Manufacturer>/<Model>/instrument.py`.  The base
package should omit `widget.py` if only the model packages should
appear in the rack picker.  See `instruments/Novanta/Opus*` for an
example of this pattern.

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

Do not use `pyqtProperty` anywhere in the codebase.

#### `_register()` helper

Instruments whose properties follow the standard DS345-style command convention (`CMD?` to query, `CMDvalue` to set) should define a `_register(name, cmd, dtype=float)` helper method to eliminate per-property boilerplate in `_registerProperties`:

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

`QSerialInstrument` provides the complete communication API for serial instruments: `transmit(data)` sends a command with no response; `handshake(cmd)` sends a command and returns the stripped response; `expect(cmd, response)` checks the response for a substring; `getValue(cmd, dtype)` returns a typed value. These helpers belong in `QSerialInstrument`, not in `QAbstractInstrument`, because they assume a command-response protocol specific to serial and GPIB-style instruments. A future `QGPIBInstrument` would provide the same API over a different physical layer.

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

Always import classes by their full module path:
```python
from QInstrument.lib.QSerialInstrument import QSerialInstrument
from QInstrument.lib.QInstrumentWidget import QInstrumentWidget
from QInstrument.lib.QFakeInstrument import QFakeInstrument
from QInstrument.lib.QPollingMixin import QPollingMixin
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

All instruments are fully migrated. The `instruments/` directory is
organised by manufacturer.

- `lib/` — fully migrated: `qtpy` throughout, `registerProperty()` API, `QInstrumentWidget` uses `device.get()`/`device.set()`; `QInstrumentTree` implemented (`pyqtgraph` optional dependency)
- `instruments/StanfordResearch/DS345/` — reference implementation: `_register()` helper, type hints, full docstrings
- `instruments/StanfordResearch/SR830/` — `QPollingMixin` (batched `SNAP?9,3,4` poll), MRO fake, `auto_offset_x/y/r` wrappers, full docstrings
- `instruments/StanfordResearch/SR844/` — `QPollingMixin` (batched `SNAP?9,3,4` poll), MRO fake, `auto_offset_x/y/r` wrappers, full docstrings
- `instruments/IPGPhotonics/IPGLaser/` — `_registerProperties()`, MRO fake with `_store` getters, `status()` batch method, `_poll`, `fault_detail()`
- `instruments/Novanta/Opus/` — base class with `WAVELENGTH`/`MINIMUM_POWER`/`MAXIMUM_POWER` class attributes; model subclasses `Opus532`, `Opus660`, `Opus1064` in sibling directories
- `instruments/PriorScientific/Proscan/` — `_registerProperties()` with explicit lambdas (comma-delimited `CMD,value` protocol), MRO fake, `QTimer` poll, `_connectSignals()` for joystick/zdial/buttons
- `instruments/PiezoDrive/PDUS210/` — `_registerProperties()`, three property groups, `state()` bulk binary read, `_toggle()` helper, MRO fake
- All `comm` dicts — long-form enum access throughout

### Not subject to migration

- `instruments/Tektronix/TDS1000/` — experimental; waveform acquisition only (no property-based control, no widget, no fake). Scope undefined.
