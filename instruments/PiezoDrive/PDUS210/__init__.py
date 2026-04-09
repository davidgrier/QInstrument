import importlib

_lazy = {'QPDUS210': 'instrument', 'QFakePDUS210': 'fake', 'QPDUS210Widget': 'widget'}

def __getattr__(name):
    if name in _lazy:
        mod = importlib.import_module(f'.{_lazy[name]}', package=__name__)
        return getattr(mod, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = list(_lazy)
