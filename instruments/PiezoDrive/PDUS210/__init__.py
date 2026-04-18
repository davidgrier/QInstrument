from QInstrument.lib.lazy import make_getattr

_lazy = {'QPDUS210': 'instrument', 'QFakePDUS210': 'fake', 'QPDUS210Widget': 'widget'}

__getattr__ = make_getattr(_lazy, __name__)
__all__ = list(_lazy)
