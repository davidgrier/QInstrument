from QInstrument.instruments.Novanta.Opus.instrument import QOpus


class QOpus1064(QOpus):
    '''Novanta Opus1064 continuous-wave laser (1064 nm, 2–10 W).'''

    WAVELENGTH: float = 1064.
    MINIMUM_POWER: float = 2000.   # mW
    MAXIMUM_POWER: float = 10000.  # mW


if __name__ == '__main__':
    QOpus1064.example()

__all__ = ['QOpus1064']
