from QInstrument.lib.lazy import make_getattr

_lazy = {
    'QSR844':       'instrument',
    'QFakeSR844':   'fake',
    'QSR844Widget': 'widget',
}

__getattr__ = make_getattr(_lazy, __name__)
__all__ = list(_lazy)
