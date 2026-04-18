from QInstrument.lib.lazy import make_getattr

_lazy = {
    'QOpus532':       'instrument',
    'QFakeOpus532':   'fake',
    'QOpus532Widget': 'widget',
}

__getattr__ = make_getattr(_lazy, __name__)
__all__ = list(_lazy)
