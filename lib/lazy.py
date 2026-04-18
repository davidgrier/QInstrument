import importlib
import sys


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


__all__ = ['make_getattr']
