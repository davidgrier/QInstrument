from QInstrument.lib.QSerialInstrument import QSerialInstrument


class QTDS1000(QSerialInstrument):

    comm = dict(baudRate=QSerialInstrument.Baud9600,
                dataBits=QSerialInstrument.Data8,
                stopBits=QSerialInstrument.OneStop,
                parity=QSerialInstrument.NoParity,
                flowControl=QSerialInstrument.HardwareControl,
                eol=b'\n')

    def __init__(self, portname=None, **kwargs):
        args = self.comm | kwargs
        super().__init__(portname, **args)

    def identify(self):
        return 'TEKTRONIX' in self.handshake('*IDN?')


def example():
    from PyQt5.QtCore import QCoreApplication
    from struct import unpack
    import numpy as np
    import matplotlib.pyplot as plt

    app = QCoreApplication([])
    scope = QTDS1000(timeout=500).find()
    print(scope.portName())
    print(scope.handshake('*IDN?'))

    scope.transmit('DATA:SOURCE CH1')
    print(scope.handshake('DATA:SOURCE?'))
    scope.transmit('DATA:WIDTH 1')
    scope.transmit('DATA:ENC RPB')
    print(scope.handshake('CH1:COUPLING?'))
    ymult = scope.get_value('WFMPRE:YMULT?')
    yzero = scope.get_value('WFMPRE:YZERO?')
    yoff = scope.get_value('WFMPRE:YOFF?')
    xincr = scope.get_value('WFMPRE:XINCR?')
    xdelay = scope.get_value('HOR:POS?')
    scope.transmit('CURVE?')
    data = scope.receive(raw=True)

    headerlen = 2 + int(data[1])
    adc = data[headerlen:-1]
    adc = np.array(unpack(f'{len(adc)}B', adc))
    signal = (adc - yoff) * ymult + yzero
    time = np.arange(0, (xincr * len(signal)), xincr)
    time -= xincr * len(signal) / 2 - xdelay

    plt.plot(time, signal)
    plt.show()


if __name__ == '__main__':
    example()
