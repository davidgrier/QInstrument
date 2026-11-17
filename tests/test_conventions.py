'''The conventions of CLAUDE.md that a machine can check.

Each rule is here because breaking it fails somewhere else, later and less
clearly: another Qt binding, a wheel that lacks a file, a documentation page
that is empty.  The scan reads the source of the package, not the tests,
the documentation, or the experimental ``Tektronix`` package.
'''
import ast
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKIP_DIRS = ('tests', 'docs', 'build', 'dist', 'Tektronix')
QT_BINDINGS = ('PyQt5', 'PyQt6', 'PySide2', 'PySide6')
SHORT_ENUMS = re.compile(
    r'\bQSerialInstrument\.(Baud\d+|Data\d|OneStop|TwoStop|OneAndHalfStop'
    r'|NoParity|EvenParity|OddParity|NoFlowControl|HardwareControl'
    r'|SoftwareControl)\b')


def sources() -> list[Path]:
    '''Return the Python files of the package, not scratch directories.'''
    found = []
    for path in sorted(ROOT.rglob('*.py')):
        parts = path.relative_to(ROOT).parts
        if any(part.startswith('.') or part in SKIP_DIRS
               or part.endswith('.egg-info') for part in parts):
            continue
        found.append(path)
    return found


def parse(path: Path) -> ast.Module:
    return ast.parse(path.read_text(), filename=str(path))


def where(path: Path, node: ast.AST) -> str:
    return f'{path.relative_to(ROOT)}:{node.lineno}'


class TestQtImports(unittest.TestCase):

    def test_qt_is_imported_through_qtpy(self):
        found = []
        for path in sources():
            for node in ast.walk(parse(path)):
                names = []
                if isinstance(node, ast.Import):
                    names = [a.name for a in node.names]
                elif isinstance(node, ast.ImportFrom) and node.module:
                    names = [node.module]
                if any(n.split('.')[0] in QT_BINDINGS
                       or n.startswith('pyqtgraph.Qt') for n in names):
                    found.append(where(path, node))
        self.assertEqual(found, [], 'import Qt through qtpy')

    def test_qtpy_comes_before_pyqtgraph(self):
        late = []
        for path in sources():
            lines = path.read_text().splitlines()
            graph = next((n for n, line in enumerate(lines, 1) if
                          re.match(r'\s*(import|from) pyqtgraph', line)),
                         None)
            if graph is None:
                continue
            qtpy = next((n for n, line in enumerate(lines, 1) if
                         re.match(r'\s*(import|from) qtpy', line)), None)
            if qtpy is None or graph < qtpy:
                late.append(f'{path.relative_to(ROOT)}:{graph}')
        self.assertEqual(late, [], 'import qtpy before pyqtgraph')


class TestPropertySystem(unittest.TestCase):

    def test_no_pyqt_names(self):
        found = []
        for path in sources():
            for node in ast.walk(parse(path)):
                name = (node.id if isinstance(node, ast.Name) else
                        node.attr if isinstance(node, ast.Attribute) else
                        node.name if isinstance(node, ast.alias) else '')
                if name in ('pyqtProperty', 'pyqtSignal', 'pyqtSlot'):
                    found.append(where(path, node))
        self.assertEqual(
            found, [],
            'use registerProperty() and QtCore.Signal and QtCore.Slot')


class TestEnums(unittest.TestCase):

    def test_serial_enums_are_scoped(self):
        found = []
        for path in sources():
            for number, line in enumerate(path.read_text().splitlines(), 1):
                if SHORT_ENUMS.search(line):
                    found.append(f'{path.relative_to(ROOT)}:{number}')
        self.assertEqual(
            found, [], 'use QSerialInstrument.BaudRate.Baud9600 and kin')


class TestImportsFromLib(unittest.TestCase):

    def test_classes_are_imported_from_their_modules(self):
        found = []
        for path in sources():
            for node in ast.walk(parse(path)):
                if (isinstance(node, ast.ImportFrom)
                        and node.module == 'QInstrument.lib'
                        and path.parent.name != 'lib'
                        and path.name != '__init__.py'):
                    found.append(where(path, node))
        self.assertEqual(
            found, [],
            'import QInstrument.lib.QName, not the module from the package')


class TestDocstrings(unittest.TestCase):

    def test_identify_has_a_docstring(self):
        found = []
        for path in sources():
            for node in ast.walk(parse(path)):
                if (isinstance(node, ast.FunctionDef)
                        and node.name == 'identify'
                        and not ast.get_docstring(node)):
                    found.append(where(path, node))
        self.assertEqual(
            found, [], 'identify() says which response it checks for')

    def test_sections_are_called_parameters(self):
        found = []
        for path in sources():
            for node in ast.walk(parse(path)):
                if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                    doc = ast.get_docstring(node) or ''
                    if re.search(r'^\s*Arguments\s*\n\s*-{3,}', doc,
                                 re.MULTILINE):
                        found.append(where(path, node))
        self.assertEqual(found, [], 'name the section Parameters')

    def test_every_public_class_has_a_docstring(self):
        found = []
        for path in sources():
            for node in ast.walk(parse(path)):
                if (isinstance(node, ast.ClassDef)
                        and not node.name.startswith('_')
                        and not ast.get_docstring(node)):
                    found.append(where(path, node))
        self.assertEqual(found, [], 'Sphinx lists only documented classes')


class TestInstrumentPackages(unittest.TestCase):

    def test_each_instrument_has_the_standard_files(self):
        found = []
        for init in sorted(ROOT.glob('instruments/*/*/__init__.py')):
            package = init.parent
            if package.parent.name == 'Tektronix':
                continue
            has_widget = (package / 'widget.py').exists()
            wanted = ['instrument.py', '__init__.py']
            if has_widget:
                wanted += ['fake.py', 'tree.py']
            found += [f'{package.relative_to(ROOT)}: no {name}'
                      for name in wanted if not (package / name).exists()]
        self.assertEqual(found, [])


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
