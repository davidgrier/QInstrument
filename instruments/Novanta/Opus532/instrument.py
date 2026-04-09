from QInstrument.instruments.Novanta.Opus.instrument import QOpus


class QOpus532(QOpus):
    '''Novanta Opus532 continuous-wave laser (532 nm, 0–6 W).'''

    WAVELENGTH: float = 532.
    MINIMUM_POWER: float = 0.
    MAXIMUM_POWER: float = 6000.   # mW


if __name__ == '__main__':
    QOpus532.example()

__all__ = ['QOpus532']
