import importlib

_lazy = {
    'QJoystick':              'QJoystick',
    'QLedWidget':             'QLedWidget',
    'QRotaryEncoder':         'QRotaryEncoder',
    'QRotaryEncoderSpinBox':  'QRotaryEncoderSpinBox',
}


def __getattr__(name):
    if name in _lazy:
        mod = importlib.import_module(f'.{_lazy[name]}', package=__name__)
        return getattr(mod, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = list(_lazy)
