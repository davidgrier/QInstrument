import importlib
import pkgutil

_subpackages: list[str] | None = None


def _get_subpackages() -> list[str]:
    global _subpackages
    if _subpackages is None:
        _subpackages = [
            name for _, name, ispkg
            in pkgutil.walk_packages(__path__, prefix=__name__ + '.')
            if ispkg
        ]
    return _subpackages


def __getattr__(name: str):
    for subpkg in _get_subpackages():
        try:
            mod = importlib.import_module(subpkg)
            if name in getattr(mod, '__all__', []):
                return getattr(mod, name)
        except ImportError:
            continue
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    'DS345',
    'IPGLaser',
    'Opus',
    'PiezoDrive',
    'Proscan',
    'SR830',
    'SR844',
    'TDS1000',
]
