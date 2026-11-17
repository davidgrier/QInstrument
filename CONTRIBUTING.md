# Contributing to QInstrument

Thank you for your interest in contributing to QInstrument.  QInstrument
exists to make it easy to control scientific instruments from Qt programs,
and the most valuable contribution is **support for another instrument**.

## What belongs in QInstrument

QInstrument is for instruments that are controlled over a serial-style
connection and that a user adjusts: function generators, lock-in amplifiers,
lasers, stages.  Cameras and what is done to their frames belong in the
sister project [QVideo](https://github.com/davidgrier/QVideo).

If you are not sure whether an idea fits, open an issue and ask before you
write code.

## Setting up a development environment

```bash
git clone https://github.com/davidgrier/QInstrument.git
cd QInstrument
python -m venv .qi && source .qi/bin/activate
pip install -e ".[dev]"        # or dev-pyqt5, dev-pyside6
pre-commit install             # ruff and the convention tests before a commit,
                               # the full suite before a push
```

No build step is required: the package is used directly from the source
tree.  Run `pip install -e ".[dev]"` again after changing the version, the
dependencies or the package list in `pyproject.toml`.

To build the documentation locally:

```bash
pip install -e ".[docs]"
sphinx-build -b html docs docs/_build/html
```

## Running the tests and the linter

```bash
python -m pytest                           # everything
python -m pytest tests/test_QDS345.py      # one file
python -m pytest --cov                     # coverage; pyproject.toml sets the floor
ruff check .                               # also runs in CI
pyright                                    # lib/ only; allowed to fail in CI
```

Tests never need hardware: every instrument is tested against its fake or
a stand-in for the serial port.  On a machine without a display, set
`QT_QPA_PLATFORM=offscreen`.

CI runs the suite on Python 3.10 to 3.14 with PyQt6 and PyQt5 (PySide6 is
experimental), runs `ruff check .`, measures coverage, and builds the wheel.
A pull request needs the tests and the linter to pass.

Some tests check the conventions of the code (`tests/test_conventions.py`:
Qt is imported through `qtpy`, properties use `registerProperty()`, serial
enums are scoped, `identify()` has a docstring) and the packaging
(`tests/test_packaging.py`: every package is listed in `pyproject.toml`, or
it is missing from the wheel).  When one of them fails, fix the code, not
the test.

## Adding an instrument

`CLAUDE.md` has the full recipe; in outline, create
`instruments/<Manufacturer>/<Name>/` with

1. `instrument.py`: the class, a `comm` dict, `identify()` with a docstring,
   and properties registered with `registerProperty()`;
2. `fake.py`, `widget.py` (with its `.ui` file), `tree.py` and `__init__.py`;
3. `"QInstrument.instruments.<Manufacturer>.<Name>"` in the `packages` list
   of `pyproject.toml` (and an `__init__.py` in a new manufacturer directory,
   which also goes in the list);
4. `tests/test_Q<Name>.py`, which mixes in `tests/instrument_contract.py`.

`instruments/StanfordResearch/DS345/` is the reference implementation.  Say
in the pull request what you tested on hardware and what only against the
fake.

## Style

- Import Qt through `qtpy`; use `QtCore.Signal`, `QtCore.Slot`.
- Single quotes, including docstrings; lines of at most 79 characters;
  `ruff check .` is the arbiter.
- NumPy-style docstrings with a `Parameters` section, and type hints on new
  code (`str | None`, not `Optional[str]`).
- Never `pyqtProperty`: instrument properties are registered.

## Changing the API

Keep the old name working for one minor release with a `DeprecationWarning`
that names the replacement, add a `CHANGELOG.md` entry under **Deprecated**
or **Changed**, and update the documentation.

## Releasing

See the Releasing section of `CLAUDE.md`.  Version and changelog are edited
by hand; `CITATION.cff` is updated by CI.
