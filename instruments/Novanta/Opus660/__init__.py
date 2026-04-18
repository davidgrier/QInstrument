from QInstrument.lib.lazy import make_getattr

_lazy = {
    'QOpus660':       'instrument',
    'QFakeOpus660':   'fake',
    'QOpus660Widget': 'widget',
}

__getattr__ = make_getattr(_lazy, __name__)
__all__ = list(_lazy)
