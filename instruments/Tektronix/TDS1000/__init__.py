from QInstrument.lib.lazy import make_getattr

_lazy = {'QTDS1000': 'instrument'}

__getattr__ = make_getattr(_lazy, __name__)
__all__ = list(_lazy)
