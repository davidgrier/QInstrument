Quick start
===========

Launch the rack application
----------------------------

The ``qinstrument`` command launches a rack that holds multiple
instrument widgets.  Pass instrument names as arguments:

.. code-block:: bash

   qinstrument DS345 SR830

With no arguments, the rack restores the last-used instrument list
from ``~/.QInstrument/QInstrumentRack.json``:

.. code-block:: bash

   qinstrument

You can also use ``python -m QInstrument`` in place of ``qinstrument``.

At runtime, click **Add instrument…** to load an instrument from the
list of available drivers, or right-click any instrument panel to
remove it.  The rack saves its instrument list on close and restores
it on next launch.

Run a single instrument widget from the command line
-----------------------------------------------------

Instrument packages are organised under manufacturer subdirectories
(e.g. ``instruments/StanfordResearch/DS345/``).  Use the full dotted
path to run a widget directly:

.. code-block:: bash

   python -m QInstrument.instruments.StanfordResearch.DS345.widget

Use a widget in your application
---------------------------------

Import classes using the full manufacturer path:

.. code-block:: python

   from qtpy.QtWidgets import QApplication
   from QInstrument.instruments.StanfordResearch.DS345 import QDS345Widget

   app = QApplication([])
   widget = QDS345Widget()
   widget.show()
   app.exec()

The widget saves the instrument's property values to
``~/.QInstrument/QDS345.json`` on close and restores them on next
launch.

Use a simulated instrument
--------------------------

When hardware is not available, pass a fake device directly:

.. code-block:: python

   from qtpy.QtWidgets import QApplication
   from QInstrument.instruments.StanfordResearch.DS345 import QDS345Widget, QFakeDS345

   app = QApplication([])
   widget = QDS345Widget(device=QFakeDS345())
   widget.show()
   app.exec()

Access instrument properties programmatically
---------------------------------------------

.. code-block:: python

   from QInstrument.instruments.StanfordResearch.DS345 import QDS345

   ds345 = QDS345().find()
   if ds345.isOpen():
       print(ds345.get('frequency'))
       ds345.set('frequency', 1000.0)
       ds345.close()

Use a parameter tree
--------------------

Each instrument also ships a :class:`~QInstrument.lib.QInstrumentTree.QInstrumentTree`
that presents all registered properties and methods in a
:class:`pyqtgraph.parametertree.ParameterTree` — no ``.ui`` file
required.  Install the optional dependency first:

.. code-block:: bash

   pip install 'QInstrument[tree]'

Then use the tree the same way as the widget:

.. code-block:: python

   from qtpy.QtWidgets import QApplication
   from QInstrument.instruments.StanfordResearch.DS345 import QDS345Tree

   app = QApplication([])
   tree = QDS345Tree()
   tree.show()
   app.exec()

Run a single tree from the command line:

.. code-block:: bash

   python -m QInstrument.instruments.StanfordResearch.DS345.tree

The tree reflects live device changes (e.g. from a polling timer) and
forwards user edits to the device.  Read-only properties are displayed
but cannot be edited; registered methods appear as buttons.

Show a subset of properties and methods
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

By default the tree displays every registered property and method.
To restrict the display, pass a ``fields`` list at instantiation time:

.. code-block:: python

   tree = QDS345Tree(fields=['frequency', 'amplitude', 'function'])

The names must match those used in :meth:`registerProperty` /
:meth:`registerMethod`.  The display order follows the list.

For a permanent per-class subset, declare :attr:`FIELDS` on the subclass:

.. code-block:: python

   class QDS345Tree(QInstrumentTree):
       INSTRUMENT = QDS345
       FIELDS = ['frequency', 'amplitude', 'function']

If any name in ``fields`` or :attr:`FIELDS` does not match a registered
property or method, a warning is logged and the full set of properties
and methods is shown instead so the instrument remains usable.

Rate-limit sensitive properties
--------------------------------

Some instruments cannot accept rapid-fire changes — a laser power
control, for example, should not be updated many times per second as
the user scrolls a spinbox.  Declare a ``debounce`` interval
(milliseconds) when registering such a property and
:class:`~QInstrument.lib.QInstrumentWidget.QInstrumentWidget` will
coalesce rapid UI changes automatically, sending only the final value
to the device once the user pauses:

.. code-block:: python

   self.registerProperty(
       'power',
       getter=self._get_power,
       setter=self._set_power,
       ptype=float,
       minimum=0., maximum=100.,
       debounce=500          # wait 500 ms after the last change
   )

No widget code is required.  Properties without ``debounce`` (or with
``debounce=0``) continue to update the device on every signal
emission, as before.
