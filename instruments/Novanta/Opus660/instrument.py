from QInstrument.instruments.Novanta.Opus.instrument import QOpus


class QOpus660(QOpus):
    '''Novanta Opus660 continuous-wave laser (660 nm, 0–1.5 W).'''

    WAVELENGTH: float = 660.
    MINIMUM_POWER: float = 0.
    MAXIMUM_POWER: float = 1500.   # mW


if __name__ == '__main__':
    QOpus660.example()

__all__ = ['QOpus660']
