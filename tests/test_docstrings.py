'''The public API is documented, so that Sphinx can publish it.

Sphinx lists only what has a docstring (there is no ``:undoc-members:``),
so an undocumented public class, function, method or property silently
disappears from the documentation.  This test says which.

A method is documented if it, or the method of a base class that it
overrides, has a docstring: Sphinx inherits docstrings the same way.
Overrides of Qt event handlers (``*Event``) are exempt, and so are Qt
signals, which are documented in the docstring of their class.
'''
import importlib
import inspect
import pkgutil
import re
import unittest

#: The packages whose public API must be documented.
PACKAGES = ('QInstrument.lib', 'QInstrument.widgets',
            'QInstrument.instruments')
MODULES = ('QInstrument.QInstrumentRack',)


def modules(package: str):
    '''Yield the modules of a package, and the package itself.'''
    pkg = importlib.import_module(package)
    yield pkg
    for info in pkgutil.walk_packages(pkg.__path__, package + '.'):
        yield importlib.import_module(info.name)


def own_doc(member) -> str:
    '''Return the docstring that a member has of its own.'''
    if isinstance(member, property):
        member = member.fget
    member = getattr(member, '__func__', member)
    return inspect.cleandoc(getattr(member, '__doc__', None) or '')


def documented(cls: type, name: str) -> bool:
    '''Whether a member of a class is documented here or in a base class
    that belongs to QInstrument.'''
    for base in cls.__mro__:
        if not getattr(base, '__module__', '').startswith('QInstrument'):
            continue
        member = base.__dict__.get(name)
        if member is not None and own_doc(member):
            return True
    return False


def is_member(value) -> bool:
    '''Whether a class attribute is something to document.'''
    unwrapped = getattr(value, '__func__', value)
    if inspect.isclass(value):
        # Not the Qt enums that a class re-exports (QSerialInstrument.BaudRate).
        return value.__module__.startswith('QInstrument')
    return inspect.isfunction(unwrapped) or isinstance(value, property)


def missing(module) -> list[str]:
    '''Return the public items of a module that have no docstring.'''
    found = []
    for name, obj in vars(module).items():
        if name.startswith('_') or getattr(obj, '__module__', None) \
                != module.__name__:
            continue
        where = f'{module.__name__}.{name}'
        if inspect.isfunction(obj):
            if not own_doc(obj):
                found.append(where)
        elif inspect.isclass(obj):
            if not (obj.__doc__ or '').strip():
                found.append(where)
            for attr, value in vars(obj).items():
                if attr.startswith('_') or attr.endswith('Event'):
                    continue
                if is_member(value) and not documented(obj, attr):
                    found.append(f'{where}.{attr}')
    return found


def parameter_names(doc: str) -> list[str] | None:
    '''Return the names that the Parameters section of a docstring lists,
    or ``None`` if it has no such section.

    In a NumPy docstring (after ``inspect.cleandoc``) an entry starts at
    the left margin, as ``name : type``, and its description is indented.
    '''
    lines = inspect.cleandoc(doc).splitlines()
    for i, line in enumerate(lines[:-1]):
        if line.strip() == 'Parameters' and set(lines[i + 1].strip()) == {'-'}:
            break
    else:
        return None
    names = []
    for j in range(i + 2, len(lines)):
        line = lines[j]
        nxt = lines[j + 1] if j + 1 < len(lines) else ''
        if nxt.strip() and set(nxt.strip()) == {'-'}:
            break                      # the next section begins
        if line and not line[0].isspace():
            names.append(line.split(':')[0].strip().lstrip('*'))
    return names


def callables(module):
    '''Yield ``(name, function, skipped)`` for the public functions and
    methods of a module, where *skipped* are the names that a docstring
    does not list (``self`` and ``cls`` of a method).'''
    for name, obj in vars(module).items():
        if name.startswith('_') or getattr(obj, '__module__', None) \
                != module.__name__:
            continue
        if inspect.isfunction(obj):
            yield f'{module.__name__}.{name}', obj, ()
        elif inspect.isclass(obj):
            for attr, value in vars(obj).items():
                value = getattr(value, '__func__', value)
                if not attr.startswith('_') and inspect.isfunction(value):
                    yield (f'{module.__name__}.{name}.{attr}', value,
                           ('self', 'cls'))


class TestDocstrings(unittest.TestCase):

    def test_the_public_api_is_documented(self):
        found = []
        for package in PACKAGES:
            for module in modules(package):
                found += missing(module)
        for name in MODULES:
            found += missing(importlib.import_module(name))
        self.assertEqual(
            found, [], 'public items without a docstring:\n  '
            + '\n  '.join(found))

    def test_no_class_docstring_has_an_inherits_section(self):
        found = []
        for package in PACKAGES:
            for module in modules(package):
                for name, obj in vars(module).items():
                    if (inspect.isclass(obj)
                            and obj.__module__ == module.__name__
                            and re.search(r'^\s*Inherits\s*$',
                                          obj.__doc__ or '', re.MULTILINE)):
                        found.append(f'{module.__name__}.{name}')
        self.assertEqual(found, [], 'the signature says what a class inherits')

    def test_parameters_sections_match_the_signature(self):
        found = []
        for package in PACKAGES:
            for module in modules(package):
                for where, func, skipped in callables(module):
                    listed = parameter_names(func.__doc__ or '')
                    if listed is None:
                        continue
                    actual = [p for p in inspect.signature(func).parameters
                              if p not in skipped]
                    if listed != actual:
                        found.append(f'{where}: documents {listed}, '
                                     f'takes {actual}')
        self.assertEqual(found, [], 'Parameters out of step with the code:\n  '
                         + '\n  '.join(found))

    def test_the_parameter_parser(self):
        doc = '''Do it.

        Parameters
        ----------
        a : int
            The first.
        *args
            Others.
        **kwargs :
            More.

        Returns
        -------
        int
            Something.
        '''
        self.assertEqual(parameter_names(doc), ['a', 'args', 'kwargs'])
        self.assertIsNone(parameter_names('No sections here.'))

    def test_the_check_sees_a_missing_docstring(self):
        class Bare:
            '''A class.'''

            def method(self):
                pass

        self.assertFalse(documented(Bare, 'method'))
        self.assertTrue(is_member(Bare.__dict__['method']))


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
