How to Add an Instrument
========================

This tutorial walks through adding a new serial instrument to QInstrument.
The reference implementation is
:class:`~QInstrument.instruments.StanfordResearch.DS345.instrument.QDS345`;
reading its source alongside this page is recommended.

The example instrument is a fictional "Acme Systems Model 1000" bench
supply with two float properties — ``voltage`` (read/write) and
``current`` (read-only) — and a single ``reset`` method.  Its serial
protocol follows the standard ``CMD?`` / ``CMDvalue`` convention.

.. contents:: Steps
   :local:
   :depth: 1

----

Step 1 — Directory structure
-----------------------------

Instruments live under ``instruments/<Manufacturer>/<Name>/``.
Create the directory tree and its ``__init__.py`` files:

.. code-block:: text

   instruments/
   └── AcmeSystems/
       ├── __init__.py           ← empty
       └── Model1000/
           ├── __init__.py
           ├── instrument.py
           ├── fake.py
           ├── widget.py
           ├── tree.py
           └── Model1000Widget.ui

If the manufacturer directory does not yet exist, add it to the
``packages`` list in ``pyproject.toml`` (see :ref:`Step 7 <step6-pyproject>`).

----

Step 2 — ``instrument.py``
--------------------------

Inherit from :class:`~QInstrument.lib.QSerialInstrument.QSerialInstrument`.
Define a ``comm`` dict with the serial parameters, call
``_registerProperties()`` from ``__init__``, and implement
``identify()``.

.. code-block:: python

   from QInstrument.lib.QSerialInstrument import QSerialInstrument


   class QModel1000(QSerialInstrument):
       '''Acme Systems Model 1000 bench supply.

       Properties
       ==========

       Control
       -------
       voltage : float [V]
           Output voltage setpoint.
           Range: 0 – 30.

       Status (read-only)
       ------------------
       current : float [A]
           Measured output current.
       '''

       comm = dict(baudRate=QSerialInstrument.BaudRate.Baud9600,
                   dataBits=QSerialInstrument.DataBits.Data8,
                   stopBits=QSerialInstrument.StopBits.OneStop,
                   parity=QSerialInstrument.Parity.NoParity,
                   flowControl=QSerialInstrument.FlowControl.NoFlowControl,
                   eol='\n')

       def _registerProperties(self) -> None:
           self._register('voltage', 'VOLT')
           self.registerProperty('current', ptype=float, setter=None,
                                 getter=lambda: self.getValue('IOUT?', float))

       def _registerMethods(self) -> None:
           self.registerMethod('reset', self.reset)

       def _register(self, name: str, cmd: str, dtype: type = float) -> None:
           '''Register a standard CMD? / CMDvalue property.'''
           def getter(): return self.getValue(f'{cmd}?', dtype)
           def setter(v): return self.transmit(f'{cmd}{dtype(v)}')
           self.registerProperty(name, getter=getter, setter=setter, ptype=dtype)

       def identify(self) -> bool:
           '''Return True if the device identifies as a Model 1000.

           Queries ``*IDN?`` and checks for ``'MODEL1000'`` in the response.
           '''
           return 'MODEL1000' in self.handshake('*IDN?')

       def reset(self) -> None:
           '''Reset the instrument to factory defaults.'''
           self.transmit('*RST')


   if __name__ == '__main__':
       QModel1000.example()

   __all__ = ['QModel1000']

**Key points**

- ``comm`` uses long-form enum access (``BaudRate.Baud9600`` etc.) via
  :class:`~QInstrument.lib.QSerialInstrument.QSerialInstrument` class
  attributes — never the short form, which fails with PyQt6.
- The ``_register()`` helper is the standard pattern for
  ``CMD?`` / ``CMDvalue`` properties.  Copy it verbatim; only the
  details differ from instrument to instrument.
- Non-standard properties (``current`` above, which queries ``IOUT?``
  but cannot be set) use :meth:`~QInstrument.lib.QAbstractInstrument.QAbstractInstrument.registerProperty`
  directly with ``setter=None``.
- ``identify()`` must return ``True`` only for the correct model.
  :meth:`~QInstrument.lib.QSerialInstrument.QSerialInstrument.find`
  calls it on each port until one succeeds.

----

Step 3 — ``fake.py``
--------------------

Inherit from both :class:`~QInstrument.lib.QFakeInstrument.QFakeInstrument`
and the instrument class (MRO order matters: fake first).
Call the real ``_registerProperties()`` so the fake mirrors every
registered property.  ``QFakeInstrument`` provides a ``_store`` dict
whose values are returned by the auto-generated getters, so most
properties need no extra code.

.. code-block:: python

   from QInstrument.lib.QFakeInstrument import QFakeInstrument
   from QInstrument.instruments.AcmeSystems.Model1000.instrument import QModel1000


   class QFakeModel1000(QFakeInstrument, QModel1000):
       '''Simulated Model 1000 for UI development without hardware.

       ``voltage`` and ``current`` are backed by ``_store``.
       ``current`` is read-only in the real instrument; the fake
       initializes it to a plausible default so the widget renders
       sensibly at startup.
       '''

       def _registerProperties(self) -> None:
           QModel1000._registerProperties(self)
           self._store.setdefault('current', 0.0)


   __all__ = ['QFakeModel1000']

**Key points**

- ``QFakeInstrument._registerProperties()`` does **not** need to be
  called explicitly; ``QModel1000._registerProperties(self)`` runs
  first and the ``_register()`` helper produces closures that call
  ``getValue()`` / ``transmit()``, which are no-ops in
  ``QFakeInstrument``.  The standard backing-attribute convention
  (``self._AUTO``) handles the rest automatically.
- Clamp the ``_store`` values for read-only status properties to
  sensible defaults so the widget has something to display.
- If any property uses non-standard getter/setter logic (like DS345's
  ``amplitude`` or ``mute``), override it in ``_registerProperties``
  to use ``_store`` directly instead of calling the wire protocol.

----

Step 4 — ``widget.py``
----------------------

Inherit from :class:`~QInstrument.lib.QInstrumentWidget.QInstrumentWidget`.
Set ``UIFILE`` to the ``.ui`` filename and ``INSTRUMENT`` to the
instrument class.  ``QInstrumentWidget.__init__`` does the rest.

.. code-block:: python

   from QInstrument.lib.QInstrumentWidget import QInstrumentWidget
   from QInstrument.instruments.AcmeSystems.Model1000.instrument import QModel1000


   class QModel1000Widget(QInstrumentWidget):
       '''Control widget for the Acme Systems Model 1000 bench supply.'''

       UIFILE = 'Model1000Widget.ui'
       INSTRUMENT = QModel1000


   if __name__ == '__main__':
       QModel1000Widget.example()

   __all__ = ['QModel1000Widget']

The ``.ui`` file path is resolved relative to the subclass's source
file, so ``UIFILE`` needs only the bare filename.

**Designing the ``.ui`` file**

Open Qt Designer and create a ``QWidget`` form.  Name each control
widget to match the property name it should bind to:

- A ``QDoubleSpinBox`` named ``voltage`` binds to the ``voltage``
  property automatically.
- A ``QLabel`` named ``current`` displays the current value
  (read-only binding; the widget is never edited by the user).

The binding is purely by name — no code is required.
:class:`~QInstrument.lib.QInstrumentWidget.QInstrumentWidget` calls
:meth:`device.get <QInstrument.lib.QAbstractInstrument.QAbstractInstrument.get>`
and :meth:`device.set <QInstrument.lib.QAbstractInstrument.QAbstractInstrument.set>`
on every matching widget.

**Registering ``minimum`` and ``maximum``**

Pass ``minimum`` and ``maximum`` to ``registerProperty()`` (or
``_register()``), and ``QInstrumentWidget`` will apply them to
``QDoubleSpinBox`` and ``QSpinBox`` widgets automatically:

.. code-block:: python

   self.registerProperty('voltage', getter=..., setter=...,
                         ptype=float, minimum=0., maximum=30.)

**Using the fake device interactively**

Add ``FAKEDEVICE`` to make ``example()`` fall back to the fake when
no hardware is found:

.. code-block:: python

   from QInstrument.instruments.AcmeSystems.Model1000.fake import QFakeModel1000

   class QModel1000Widget(QInstrumentWidget):
       UIFILE = 'Model1000Widget.ui'
       INSTRUMENT = QModel1000
       FAKEDEVICE = QFakeModel1000

----

Step 5 — ``tree.py``
--------------------

The parameter tree requires only two lines:

.. code-block:: python

   from QInstrument.lib.QInstrumentTree import QInstrumentTree
   from QInstrument.instruments.AcmeSystems.Model1000.instrument import QModel1000


   class QModel1000Tree(QInstrumentTree):
       '''Parameter tree for the Acme Systems Model 1000 bench supply.'''

       INSTRUMENT = QModel1000


   if __name__ == '__main__':
       QModel1000Tree.example()

   __all__ = ['QModel1000Tree']

The tree discovers all registered properties and methods at runtime.
No ``.ui`` file or layout code is needed.  ``pyqtgraph`` must be
installed (``pip install 'QInstrument[tree]'``).

----

Step 6 — ``__init__.py``
------------------------

Use lazy imports so the package is importable without triggering Qt:

.. code-block:: python

   import importlib

   _lazy = {
       'QModel1000':       'instrument',
       'QFakeModel1000':   'fake',
       'QModel1000Widget': 'widget',
   }

   def __getattr__(name):
       if name in _lazy:
           mod = importlib.import_module(f'.{_lazy[name]}', package=__name__)
           return getattr(mod, name)
       raise AttributeError(f'module {__name__!r} has no attribute {name!r}')

   __all__ = list(_lazy)

----

.. _step6-pyproject:

Step 7 — ``pyproject.toml``
---------------------------

Add both the manufacturer and model packages to the ``packages`` list:

.. code-block:: text

   [tool.setuptools]
   packages = [
       ...existing entries...,
       "QInstrument.instruments.AcmeSystems",
       "QInstrument.instruments.AcmeSystems.Model1000",
   ]

Re-install the package in editable mode to pick up the changes:

.. code-block:: bash

   pip install -e ".[dev]"

----

Step 8 — Test it
----------------

**Run the widget directly:**

.. code-block:: bash

   python -m QInstrument.instruments.AcmeSystems.Model1000.widget

With no hardware connected the widget opens in a disconnected state.
Pass a fake device explicitly for a fully interactive test:

.. code-block:: python

   from qtpy.QtWidgets import QApplication
   from QInstrument.instruments.AcmeSystems.Model1000 import (
       QModel1000Widget, QFakeModel1000)

   app = QApplication([])
   widget = QModel1000Widget(device=QFakeModel1000())
   widget.show()
   app.exec()

**Add the instrument to the rack:**

.. code-block:: bash

   qinstrument Model1000
   qinstrument --fake Model1000   # use the fake device

**Verify auto-discovery:**

.. code-block:: python

   from QInstrument.QInstrumentRack import QInstrumentRack
   print(QInstrumentRack.availableInstruments())
   # 'Model1000' should appear in the list

----

Instruments that share a protocol
----------------------------------

When several models differ only in hardware constants (power limits,
wavelength, number of channels, etc.), define the shared logic in a
*base package* and put the model-specific constants as class attributes
on thin subclasses in sibling packages.  See
``instruments/Novanta/Opus*`` for a worked example:

.. code-block:: text

   instruments/Novanta/
   ├── Opus/           ← base package (no widget.py — not shown in picker)
   │   ├── instrument.py   QOpus base class
   │   ├── fake.py
   │   └── widget.py
   ├── Opus532/        ← model subclass
   │   ├── instrument.py   class QOpus532(QOpus): WAVELENGTH = 532; ...
   │   ├── fake.py
   │   ├── widget.py
   │   └── tree.py
   ├── Opus660/
   └── Opus1064/

The base package may omit ``widget.py`` so it does not appear in the
"Add instrument…" picker; only the concrete model packages do.
