# QInstrument — Future Work

Ideas for upgrades and extensions, in no particular order.

## Type checking

`pyright` (pinned to 1.1.414) checks `lib/` with an empty report (2026-11-17).
Widgets and instrument widgets read their attributes from `.ui` files, which
pyright cannot see, so they are not included; the instruments are not yet
included either (`TDS1000` is the main obstacle).

## Coverage

The floor is 79% and the measured coverage 80% (2026-11-17).  What is left is
mostly the instrument classes (`DS345`, `IPGLaser`, `Opus`, `Proscan`,
`SR830`, `SR844`: the methods that talk to the hardware, to be tested against
a scripted serial stand-in), `Proscan`'s widget and `QInstrumentRack`'s mouse
handling.  Raise `fail_under` in `pyproject.toml` as they get tests.
