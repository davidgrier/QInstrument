from QInstrument.lib.lazy import make_getattr

_lazy = {
    'QOpus1064':       'instrument',
    'QFakeOpus1064':   'fake',
    'QOpus1064Widget': 'widget',
}

__getattr__ = make_getattr(_lazy, __name__)
__all__ = list(_lazy)
