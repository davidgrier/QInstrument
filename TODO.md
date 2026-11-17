# QInstrument — Future Work

Ideas for upgrades and extensions, in no particular order.

## Type checking

`pyright` (pinned to 1.1.414, run on `lib/`) reports 48 errors, and its CI
job is allowed to fail until the report is empty (2026-11-17).  Then drop
`continue-on-error` from the `types` job in `.github/workflows/tests.yml`.
Most are `QByteArray`/`bytes` conversions in `QSerialInterface`, `str | bytes`
returns of `receive()`, and mixin attributes in `QPollingMixin` and
`Configure` that the checker cannot see.  The widgets and instrument widgets
read their attributes from `.ui` files and are not checked.

## Coverage

The floor is 50% and the measured coverage 54% (2026-11-17).  The fakes,
widgets (`QJoystick`, `QJoystickPad`, `QLedWidget`, `QRotaryEncoderSpinBox`)
and trees have no tests.  Raise `fail_under` in `pyproject.toml` as they get
them.

## Python floor

`requires-python` is still 3.10; QVideo and QHOT require 3.11.  Raising it
would drop the `tomli` dependency of the tests and a CI leg.
