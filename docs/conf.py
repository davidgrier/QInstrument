import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

project = 'QInstrument'
author = 'David G. Grier'
copyright = '2022, David G. Grier'
release = '0.4.0'

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinx.ext.intersphinx',
    'sphinx_autodoc_typehints',
]

# Qt is not available on the RTD build server; mock all Qt-related imports
autodoc_mock_imports = [
    'PyQt5',
    'PyQt6',
    'PySide2',
    'PySide6',
    'qtpy',
    'numpy',
]

autodoc_default_options = {
    'members': True,
    'undoc-members': False,
    'show-inheritance': True,
}


napoleon_numpy_docstring = True
napoleon_google_docstring = False

intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'numpy': ('https://numpy.org/doc/stable', None),
}

html_theme = 'sphinx_rtd_theme'
html_static_path = []
