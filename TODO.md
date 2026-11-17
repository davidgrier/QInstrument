# QInstrument — Future Work

Ideas for upgrades and extensions, in no particular order.

## Type checking

`pyright` (pinned to 1.1.414) checks `lib/` with an empty report (2026-11-17).
Widgets and instrument widgets read their attributes from `.ui` files, which
pyright cannot see, so they are not included; the instruments are not yet
included either (`TDS1000` is the main obstacle).

## Coverage

The floor is 50% and the measured coverage 54% (2026-11-17).  The fakes,
widgets (`QJoystick`, `QJoystickPad`, `QLedWidget`, `QRotaryEncoderSpinBox`)
and trees have no tests.  Raise `fail_under` in `pyproject.toml` as they get
them.

## Python floor

`requires-python` is still 3.10; QVideo and QHOT require 3.11.  Raising it
would drop the `tomli` dependency of the tests and a CI leg.
