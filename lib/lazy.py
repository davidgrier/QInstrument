import importlib
import inspect
import math
import sys
from pathlib import Path


def values_differ(a: object, b: object) -> bool:
    '''Return True if *a* and *b* represent meaningfully different values.

    Floats are compared with a relative tolerance of 1e-6 and an
    absolute tolerance of 1e-9 to avoid spurious mismatches from
    JSON round-tripping.  All other types use exact equality.

    Parameters
    ----------
    a : object
        First value.
    b : object
        Second value.

    Returns
    -------
    bool
        ``True`` if the values are meaningfully different.
    '''
    if isinstance(a, float) and isinstance(b, float):
        return not math.isclose(a, b, rel_tol=1e-6, abs_tol=1e-9)
    return a != b


def find_fake_cls(cls: type) -> type | None:
    '''Return the fake instrument class from the sibling ``fake`` module.

    Looks for a ``fake.py`` in the same package as *cls* and returns the
    class named in its ``__all__``.  Returns ``None`` if no ``fake``
    module exists.

    Works when *cls* is imported normally and when its module is run
    directly as ``__main__``.

    Parameters
    ----------
    cls : type
        Widget or tree class whose sibling ``fake`` module to search.

    Returns
    -------
    type or None
        The fake instrument class, or ``None`` if unavailable.
    '''
    module = inspect.getmodule(cls)
    package = getattr(module, '__package__', None)

    if not package:
        cls_dir = Path(inspect.getfile(cls)).parent
        for entry in sys.path:
            if not entry:
                continue
            try:
                parts = cls_dir.relative_to(entry).parts
                if parts:
                    package = '.'.join(parts)
                    break
            except ValueError:
                continue

    if not package:
        return None
    try:
        fake_mod = importlib.import_module('.fake', package=package)
    except ImportError:
        return None
    return getattr(fake_mod, fake_mod.__all__[0])


def make_getattr(lazy: dict, package: str):
    '''Return a module ``__getattr__`` for lazy attribute resolution.

    Parameters
    ----------
    lazy : dict
        Mapping of attribute name to submodule path (relative to
        ``package``).  For example ``{'QDS345': 'instrument'}``.
    package : str
        Fully-qualified name of the package whose ``__getattr__``
        is being created.  Pass ``__name__`` from the caller.

    Returns
    -------
    callable
        A ``__getattr__(name)`` function suitable for assignment at
        module level.

    Notes
    -----
    The resolved value is written back into the package ``__dict__``
    after the first lookup.  This prevents Python's import machinery
    from shadowing the resolved value with the submodule object on
    subsequent accesses — a collision that occurs whenever the
    attribute name matches the submodule filename.

    Examples
    --------
    In a package ``__init__.py``::

        from QInstrument.lib.lazy import make_getattr

        _lazy = {'QDS345': 'instrument', 'QDS345Widget': 'widget'}

        __getattr__ = make_getattr(_lazy, __name__)
        __all__ = list(_lazy)
    '''
    def __getattr__(name: str):
        if name in lazy:
            mod = importlib.import_module(f'.{lazy[name]}', package=package)
            value = getattr(mod, name)
            sys.modules[package].__dict__[name] = value
            return value
        raise AttributeError(f"module {package!r} has no attribute {name!r}")
    return __getattr__


__all__ = ['values_differ', 'find_fake_cls', 'make_getattr']
