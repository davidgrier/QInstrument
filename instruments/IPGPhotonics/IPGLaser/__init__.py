from QInstrument.lib.lazy import make_getattr

_lazy = {'QIPGLaser': 'instrument', 'QFakeIPGLaser': 'fake', 'QIPGLaserWidget': 'widget'}

__getattr__ = make_getattr(_lazy, __name__)
__all__ = list(_lazy)
