from QInstrument.lib.QSerialInstrument import QSerialInstrument
import numpy as np
from struct import unpack


class QTDS1000(QSerialInstrument):

    comm = dict(baudRate=QSerialInstrument.Baud9600,
                dataBits=QSerialInstrument.Data8,
                stopBits=QSerialInstrument.OneStop,
                parity=QSerialInstrument.NoParity,
                flowControl=QSerialInstrument.HardwareControl,
                eol=b'\n')

    def __init__(self, portname=None, timeout=500, **kwargs):
        args = self.comm | kwargs
        super().__init__(portname, timeout=timeout, **args)

    def identify(self):
        return 'TEKTRONIX' in self.handshake('*IDN?')

    def data(self, channel='CH1'):
        self.transmit(f'DATA:SOURCE {channel}')
        self.transmit('DATA:WIDTH 1')
        self.transmit('DATA:ENC RPB')
        adc0 = self.get_value('WFMPRE:YOFF?')
        dx = self.get_value('WFMPRE:XINCR?')
        x0 = self.get_value('HOR:POS?')
        scale = self.get_value('WFMPRE:YMULT?')
        y0 = self.get_value('WFMPRE:YZERO?')
        self.transmit('CURVE?')
        data = self.receive(raw=True)
        headerlen = 2 + int(data[1])
        adc = data[headerlen:-1]
        npts = len(adc)
        range = dx*npts/2.
        x = np.arange(-range, range, dx) + x0
        adc = np.array(unpack(f'{npts}B', adc))
        y = scale*(adc - adc0) + y0
        return x, y


def example():
    from PyQt5.QtCore import QCoreApplication
    import matplotlib.pyplot as plt

    app = QCoreApplication([])
    scope = QTDS1000().find()
    t, s = scope.data('CH1')
    plt.plot(t, s)
    plt.xlabel('time [s]')
    plt.ylabel('signal [V]')
    plt.show()
    data = np.vstack([t, s])
    np.savetxt('tds1000.csv', data, delimiter=',')


if __name__ == '__main__':
    example()
