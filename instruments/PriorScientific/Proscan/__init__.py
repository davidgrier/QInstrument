from QInstrument.lib.lazy import make_getattr

_lazy = {'QProscan': 'instrument', 'QFakeProscan': 'fake', 'QProscanWidget': 'widget'}

__getattr__ = make_getattr(_lazy, __name__)
__all__ = list(_lazy)
