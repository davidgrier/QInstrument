Installation
============

Requirements
------------

- Python 3.10 or later
- A Qt binding: PyQt5, PyQt6, PySide2, or PySide6
- ``qtpy >= 2.0``
- ``numpy >= 1.20``

Install from PyPI
-----------------

.. code-block:: bash

   pip install QInstrument

A Qt binding is not installed automatically.  Install one separately,
for example::

   pip install PyQt6

Installing from PyPI also places a ``qinstrument`` command on your
PATH that launches the rack application.

Install from source
-------------------

.. code-block:: bash

   git clone https://github.com/davidgrier/QInstrument
   cd QInstrument
   python -m venv .qi
   source .qi/bin/activate
   pip install -e ".[dev]"
