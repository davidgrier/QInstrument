from QInstrument.lib.lazy import make_getattr

_lazy = {'QDS345': 'instrument', 'QFakeDS345': 'fake', 'QDS345Widget': 'widget'}

__getattr__ = make_getattr(_lazy, __name__)
__all__ = list(_lazy)
