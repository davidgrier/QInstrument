from QInstrument.lib.lazy import make_getattr

_lazy = {
    'QSR830':       'instrument',
    'QFakeSR830':   'fake',
    'QSR830Widget': 'widget',
}

__getattr__ = make_getattr(_lazy, __name__)
__all__ = list(_lazy)
