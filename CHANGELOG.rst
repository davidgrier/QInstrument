Changelog
=========

All notable changes to QInstrument are documented here.
The format follows `Keep a Changelog <https://keepachangelog.com>`_.

.. _v3.0.2:

3.0.2 — 2026-04-29
-------------------

Fixed
~~~~~

- ``lib/QInstrumentWidget``, ``lib/QInstrumentTree``: ``_firstShow()``
  now calls ``_syncProperties()`` *before* ``_startDeviceThread()``.
  Previously the sync ran after the device was moved to its worker
  thread; because ``_syncProperties()`` uses direct Python method calls
  (not Qt queued slots), the serial I/O executed on the main thread
  while the ``QSerialPort`` was owned by the worker thread.  This
  triggered Qt's "QSocketNotifier: cannot be enabled from another
  thread" warning, caused ``waitForReadyRead()`` to fail, and left
  every property getter returning ``None`` — producing errors such as
  "Could not set harmonic to None" and locking the UI.  Running the
  sync on the main thread (before the move) eliminates the
  cross-thread access entirely.

.. _v3.0.1:

3.0.1 — 2026-04-29
-------------------

Fixed
~~~~~

- ``lib/QInstrumentWidget``, ``lib/QInstrumentTree``: removed automatic
  ``startPolling()`` call from ``_firstShow()``.  Auto-polling caused a
  race condition when SR830/SR844 instruments were embedded in
  scan-driven applications that also called ``report()`` from the main
  thread.  Callers that need continuous updates must now invoke
  ``startPolling()`` explicitly (via
  ``QMetaObject.invokeMethod(device, 'startPolling', QueuedConnection)``
  so it executes on the worker thread).

Changed
~~~~~~~

- ``instruments/StanfordResearch/SR830``,
  ``instruments/StanfordResearch/SR844``: removed ``x``, ``y``, ``r``,
  and ``theta`` from the property registry and dropped ``QPollingMixin``
  from the class hierarchy.  Both instruments are now pure control panels
  (sensitivity, time constant, frequency, etc.), consistent with their
  widgets and trees.  The ``report()`` method remains as the measurement
  API for embedding applications.  SR844 additionally drops
  ``reference_frequency`` and ``if_frequency``.

- ``instruments/PriorScientific/Proscan``: ``QProscan`` now inherits
  ``QPollingMixin`` and implements ``_poll()`` — each cycle queries
  ``position()`` and ``active_limits()``, emitting ``positionChanged``
  and a new ``limitsChanged`` signal.  ``POLL_INTERVAL`` defaults to
  200 ms.  ``QProscanWidget`` drops its main-thread ``QTimer`` and
  cross-thread direct calls; it now connects to the device signals and
  starts polling via ``invokeMethod(QueuedConnection)`` in
  ``_firstShow()``, keeping all serial I/O on the worker thread.

- ``lib/QPollingMixin``: updated docstring to reflect that
  ``startPolling()`` must be called explicitly; it is no longer
  started automatically by ``QInstrumentWidget`` or ``QInstrumentTree``.

.. _v3.0.0:

3.0.0 — 2026-04-29
-------------------

Changed
~~~~~~~

- ``lib/QSerialInterface.py``: non-blocking mode removed entirely.
  The ``blocking`` property, ``dataReady`` signal, ``_buffer``, and
  ``_handleReadyRead`` slot have been deleted.  ``receive()`` and
  ``readn()`` use ``waitForReadyRead()`` directly and are intended to
  run in a dedicated worker thread rather than on the GUI thread.
  The ``QEventLoop``-based approach introduced in 2.4.0 has been
  reverted; ``waitForReadyRead()`` is safe in a worker thread and
  avoids reentrancy hazards.
- ``lib/QSerialInstrument.py``: ``QSerialInterface`` is now constructed
  as a Qt child of the instrument (``parent=self``), so it migrates
  automatically when the instrument is moved to a worker thread.
- ``lib/QInstrumentWidget.py``: on first show, the device is moved to a
  dedicated ``QThread`` so serial I/O no longer competes with the GUI
  event loop.  Property sync is now fire-and-forget (``device.get()``);
  values are delivered asynchronously via the ``propertyValue`` signal
  to a new ``_onPropertyValue`` slot that applies them with signals
  blocked.  ``closeEvent`` stops the thread before saving settings.
- ``lib/QInstrumentTree.py``: full parity with ``QInstrumentWidget`` —
  same first-show threading lifecycle, ``_restoreSettings()`` with
  ``QReconcileDialog``, and ``closeEvent`` save.  ``HARDWARE_DOMINANT``
  class attribute added.
- ``lib/Configure.py``: ``save()`` accepts an optional ``settings``
  parameter to avoid cross-thread reads when the device lives in a
  worker thread.
- ``lib/lazy.py``: ``values_differ()`` extracted from
  ``QInstrumentWidget`` (was duplicated) and exported in ``__all__``.
  ``find_fake_cls()`` added to ``__all__``.
- ``lib/QAbstractInstrument.py``: ``handshake()``, ``expect()``, and
  ``getValue()`` moved to ``QSerialInstrument``.
  ``QAbstractInstrument`` now has no concept of hardware communication;
  it models only instrument state (property and method registry).  A
  future transport subclass (e.g. ``QGPIBInstrument``) would provide
  the same communication helpers over a different physical layer.
- ``lib/QAbstractInstrument.py``: ``persist`` metadata flag removed
  from ``settings`` getter and setter.  The base class now treats all
  writable properties as persistent.  Instruments that need to exclude
  specific properties from save/restore should override ``settings``
  in the instrument subclass (see ``QProscan``).
- ``instruments/PriorScientific/Proscan/instrument.py``: ``speed`` and
  ``zspeed`` are excluded from save/restore via a ``settings`` override
  and a ``_VOLATILE`` class attribute, replacing the former
  ``persist=False`` argument to ``registerProperty()``.
- ``lib/QInstrumentWidget.py``: ``_firstShow()`` now invokes
  ``startPolling`` via a queued ``QMetaObject.invokeMethod`` call after
  moving the device to its worker thread, if the device inherits
  :class:`QPollingMixin`.  ``closeEvent()`` calls ``stopPolling()``
  before stopping the thread when the device supports it.
- ``lib/QInstrumentTree.py``: same polling integration as
  ``QInstrumentWidget``.
- ``instruments/StanfordResearch/SR830/instrument.py``: ``QSR830`` now
  inherits :class:`QPollingMixin` and overrides ``_poll()`` to use the
  ``SNAP?9,3,4`` batch command, emitting ``frequency``, ``r``, and
  ``theta`` as ``propertyValue`` signals on every tick.
- ``instruments/StanfordResearch/SR844/instrument.py``: same as SR830.

Added
~~~~~

- ``lib/QPollingMixin.py``: new mixin class that adds a self-scheduling
  poll loop to any instrument.  ``startPolling()`` begins the loop;
  ``stopPolling()`` ends it (safe to call from any thread).  The loop
  uses ``QTimer.singleShot`` so the next query starts only after the
  current one completes, preventing query backup under any load.
  ``POLL_INTERVAL`` (default ``0``) sets the delay between the end of
  one response and the start of the next.  The default ``_poll()``
  calls ``get()`` for every registered property; instruments that can
  batch multiple properties into a single query should override it.

Removed
~~~~~~~

- ``lib/QInstrumentWorker.py``: ``QInstrumentWorker`` removed.
  Use :class:`QPollingMixin` on the instrument class instead.
- ``instruments/StanfordResearch/SR830/worker.py``: ``QSR830Worker``
  removed.  Polling is now handled by ``QSR830._poll()``.
- ``instruments/StanfordResearch/SR844/worker.py``: ``QSR844Worker``
  removed.  Polling is now handled by ``QSR844._poll()``.

.. _v2.4.1:

2.4.1
-----

Fixed
~~~~~

- ``lib/QSerialInterface.py``: ``receive()`` now decodes bytes with
  ``errors='replace'`` instead of the strict default.  Prevents a
  ``UnicodeDecodeError`` when ``find()`` scans a port occupied by an
  instrument that responds to ``*IDN?`` with non-UTF-8 bytes.

.. _v2.4.0:

2.4.0
-----

Changed
~~~~~~~

- ``lib/QSerialInterface.py``: ``receive()`` and ``readn()`` switched
  from ``waitForReadyRead()`` to a scoped ``QEventLoop`` driven by
  ``readyRead`` and a ``QTimer``.  (This approach was reverted in the
  following release; see *Unreleased* above.)

Deprecated
~~~~~~~~~~

- ``lib/QInstrumentWorker.py``: ``QInstrumentWorker`` is deprecated and
  will be removed in a future release.

.. _v2.3.2:

2.3.2
-----

Fixed
~~~~~

- ``lib/QInstrumentWidget.py``: ``showEvent`` now defers first-show
  reconciliation via ``QTimer.singleShot(0, ...)`` instead of calling
  ``_restoreSettings()`` synchronously.  Opening a ``QReconcileDialog``
  (nested ``exec()`` event loop) from inside Qt's show-event sequence
  caused a segfault on all platforms; the deferred call runs after the
  show sequence completes, eliminating the re-entrancy.

.. _v2.3.1:

2.3.1
-----

Fixed
~~~~~

- ``lib/lazy.py``: new ``make_getattr(lazy, package)`` factory replaces
  the hand-written ``__getattr__`` boilerplate in every instrument
  ``__init__.py``.  The resolved value is cached back into the package
  ``__dict__`` via ``sys.modules[package].__dict__``, preventing
  Python's import machinery from shadowing it with the submodule object
  on subsequent accesses.  All eleven leaf instrument packages updated
  to use the factory.

.. _v2.3.0:

2.3.0
-----

Added
~~~~~

- ``instruments/__init__.py``: dynamic ``__getattr__`` aggregates all
  instrument classes from subpackages via ``pkgutil.walk_packages``.
  Instrument classes can now be imported directly from
  ``QInstrument.instruments`` (e.g.
  ``from QInstrument.instruments import QDS345Widget, QFakeSR830``)
  without specifying the full subpackage path.  Adding a new instrument
  requires no changes to ``instruments/__init__.py``.

.. _v2.2.0:

2.2.0
-----

Added
~~~~~

- ``QAbstractInstrument.registerProperty`` accepts a ``persist`` keyword
  (default ``True``).  Properties with ``persist=False`` are excluded
  from ``settings`` and never written to or restored from configuration
  files.  ``Proscan``: ``speed`` and ``zspeed`` set to ``persist=False``.
- ``Configure.read()`` reads the saved JSON without applying it, enabling
  comparison before commit.
- ``QInstrumentWidget._restoreSettings()``: on first show, hardware state
  is compared against the saved configuration.  If no file exists the
  hardware state is saved; if values match nothing happens; if they differ
  a ``QReconcileDialog`` is shown so the user can choose which values to
  adopt.  ``HARDWARE_DOMINANT = True`` on ``QProscanWidget`` makes "Keep
  Hardware" the default button.
- ``QInstrumentWorker``: runs an instrument in a dedicated ``QThread``
  with a zero-interval poll loop.  ``QSR830Worker`` and ``QSR844Worker``
  emit ``[frequency, R, theta]`` via ``SNAP?9,3,4``.
- Opus laser: ``STATUS?`` property returns ``True`` (ENABLED) or
  ``False`` (DISABLED); logs a ``WARNING`` when ``DISABLED`` is received.
- Opus laser: ``CONTROL=POWER`` sent in ``identify()`` to establish
  power-control mode on every connection.

Fixed
~~~~~

- ``QLedWidget`` rewritten to use ``QPainter`` instead of ``QSvgRenderer``.
  Eliminates the ``QtSvg`` dependency and fixes a silent packaging bug
  where ``QLedWidget.svg`` was never included in the distributed wheel,
  causing ``FileNotFoundError`` on construction for PyPI installs.
- Opus laser: ``POWER=``, ``CURRENT=``, ``ON``, and ``OFF`` setters now
  call ``handshake()`` instead of ``transmit()``, consuming the
  acknowledgement response and preventing read desynchronisation.
- ``QInstrumentWidget.set()``: replaced ``blockSignals(True/False)`` pair
  with ``QSignalBlocker`` so signals are correctly restored even if the
  setter raises.

.. _v2.1.0:

2.1.0
-----

Added
~~~~~

- ``QInstrumentRack`` now supports drag-to-reorder instrument slots.
  A ``⋮`` drag handle appears on each slot; dragging highlights the
  target with a colored bar and commits the move on release.
- ``QInstrumentRack`` close button (``×``) overlaid on each slot.
- ``QInstrumentRack.editable`` property (default ``True``) hides or
  shows the toolbar, drag handles, and close buttons as a unit.
  Set ``editable=False`` for embedded rack contexts where the
  instrument set should be fixed.
- ``-f`` / ``--fake`` command-line flag for the ``qinstrument`` CLI
  and ``QInstrumentRack.example()``: loads all instruments in fake
  (simulated) mode without probing hardware.  The flag is remembered
  by the rack, so instruments added interactively via the picker
  dialog also use fake devices.
- ``QLedWidget``: disabled widgets now render as ``WHITE/OFF``
  (grayed out) regardless of their current color.  Re-enabling
  restores the original color and state.
- Tests: ``QInstrumentRack``, ``QLedWidget``, and
  ``QRotaryEncoderSpinBox`` now have pytest coverage.

Fixed
~~~~~

- Opus widget: poll timer is no longer started when the device port
  is not open, preventing spurious "Cannot send data: device is not
  open" log messages at startup.
- Opus widget: ``maximum_power`` is now initialized from the model
  subclass constant (``MAXIMUM_POWER``) rather than a hard-coded
  default.

.. _v2.0.0:

2.0.0
-----

Added
~~~~~

- Instruments are now organized in a two-level manufacturer hierarchy:
  ``instruments/<Manufacturer>/<Name>/``.  The instrument picker in
  ``QInstrumentRack`` discovers all packages that contain a
  ``widget.py`` at this depth.
- Novanta Opus family: ``Opus`` base class plus ``Opus532``,
  ``Opus660``, and ``Opus1064`` model subclasses.  Each subclass
  sets ``WAVELENGTH``, ``MINIMUM_POWER``, and ``MAXIMUM_POWER`` as
  class attributes — no code duplication.
- ``QInstrumentRack``: "Add instrument…" toolbar button that opens a
  picker dialog listing all discovered instrument widgets.
- ``QInstrumentRack``: right-click context menu on each instrument
  slot to remove it at runtime.

Changed
~~~~~~~

- All existing instrument packages moved to their manufacturer
  subdirectory.  Import paths change from
  ``QInstrument.instruments.<Name>`` to
  ``QInstrument.instruments.<Manufacturer>.<Name>``.

.. _v1.3.0:

1.3.0
-----

Added
~~~~~

- ``QInstrumentTree``: a ``pyqtgraph`` ``ParameterTree``-based
  inspector that presents all registered properties and methods for
  any instrument without requiring a ``.ui`` file.  Properties are
  editable live; methods appear as buttons.  Read-only properties are
  displayed but cannot be edited.
- ``tree.py`` module added to each instrument package (``QDS345Tree``,
  ``QSR830Tree``, ``QOpusTree``, etc.).
- ``[tree]`` optional dependency (``pip install 'QInstrument[tree]'``)
  pulls in ``pyqtgraph>=0.13``.
- ``QInstrumentTree.fields`` / ``FIELDS``: restrict the parameter tree
  to a named subset of properties and methods.

.. _v1.2.0:

1.2.0
-----

Added
~~~~~

- ``registerProperty`` accepts a ``debounce`` keyword (milliseconds).
  ``QInstrumentWidget`` coalesces rapid UI changes and sends only the
  final value to the device after the user pauses.  Designed for
  controls (e.g. laser power) that must not receive a rapid stream of
  intermediate values.
- ``QJoystick``: ``padColor`` and ``knobColor`` style properties,
  ``setRange()`` method, and several paint-event improvements.

Changed
~~~~~~~

- IPGLaser widget overhauled: LED fault indicator, aiming-beam toggle,
  emission toggle, and improved status polling.

.. _v1.1.0:

1.1.0
-----

Added
~~~~~

- ``QInstrumentRack``: top-level widget that holds multiple
  ``QInstrumentWidget`` instances in a vertical layout.
- ``qinstrument`` CLI entry point (also invokable as
  ``python -m QInstrument``).  With no arguments it restores the last
  session; with instrument names it loads those instruments.
- Instrument list is persisted to ``~/.QInstrument/QInstrumentRack.json``
  on close and restored on next launch.

.. _v1.0.2:

1.0.2
-----

Fixed
~~~~~

- ``QSerialInterface``: corrected PyQt6 compatibility — integer enum
  values are now accessed via the long-form scoped path
  (``BaudRate.Baud9600``, etc.) throughout.

.. _v1.0.1:

1.0.1
-----

Added
~~~~~

- GitHub Actions CI workflow: runs the full test suite on push/PR.

.. _v1.0.0:

1.0.0
-----

Added
~~~~~

- PiezoDrive PDUS210 ultrasonic amplifier: fully migrated to the
  ``registerProperty()`` API with fake device and widget.
- ``Configure``: JSON-based save/restore gated on the ``_shown``
  flag so test widgets closed during teardown do not write config
  files.
- Expanded pytest suite covering ``QSerialInterface`` and
  ``QInstrumentWidget`` auto-binding.

.. _v0.4.0:

0.4.0
-----

Added
~~~~~

- ``pyproject.toml``-based packaging; installable from PyPI as
  ``pip install QInstrument``.
- Initial Sphinx documentation published to Read the Docs.
- ``pytest`` test suite.
- ``LICENSE.md`` (GPLv3).
