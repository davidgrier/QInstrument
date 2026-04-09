import importlib

_lazy = {
    'QOpus532':       'instrument',
    'QFakeOpus532':   'fake',
    'QOpus532Widget': 'widget',
}

def __getattr__(name):
    if name in _lazy:
        mod = importlib.import_module(f'.{_lazy[name]}', package=__name__)
        return getattr(mod, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = list(_lazy)
