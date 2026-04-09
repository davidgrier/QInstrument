import importlib

_lazy = {'QSR844': 'instrument', 'QFakeSR844': 'fake', 'QSR844Widget': 'widget'}

def __getattr__(name):
    if name in _lazy:
        mod = importlib.import_module(f'.{_lazy[name]}', package=__name__)
        return getattr(mod, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = list(_lazy)
