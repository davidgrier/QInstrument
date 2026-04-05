Quick start
===========

Run an instrument widget from the command line
----------------------------------------------

Each instrument widget has a built-in entry point.  This finds a connected
DS345 function generator and opens its control panel.  If no instrument is
detected it falls back to a simulated device automatically:

.. code-block:: bash

   python -m QInstrument.instruments.DS345.widget

Use a widget in your application
---------------------------------

.. code-block:: python

   from qtpy.QtWidgets import QApplication
   from QInstrument.instruments.DS345 import QDS345Widget

   app = QApplication([])
   widget = QDS345Widget()
   widget.show()
   app.exec()

Use a simulated instrument
--------------------------

When hardware is not available, pass a fake device directly:

.. code-block:: python

   from qtpy.QtWidgets import QApplication
   from QInstrument.instruments.DS345 import QDS345Widget, QFakeDS345

   app = QApplication([])
   widget = QDS345Widget(device=QFakeDS345())
   widget.show()
   app.exec()

Access instrument properties programmatically
---------------------------------------------

.. code-block:: python

   from QInstrument.instruments.DS345 import QDS345

   ds345 = QDS345().find()
   if ds345.isOpen():
       print(ds345.get('frequency'))
       ds345.set('frequency', 1000.0)
       ds345.close()
