from QInstrument.lib.lazy import make_getattr

_lazy = {'QOpus': 'instrument', 'QFakeOpus': 'fake', 'QOpusWidget': 'widget'}

__getattr__ = make_getattr(_lazy, __name__)
__all__ = list(_lazy)
