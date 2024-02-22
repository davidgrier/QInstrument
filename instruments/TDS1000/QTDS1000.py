from QInstrument.lib.QSerialInstrument import QSerialInstrument


class QTDS1000(QSerialInstrument):

    comm = dict(baudRate=QSerialInstrument.Baud9600,
                dataBits=QSerialInstrument.Data8,
                stopBits=QSerialInstrument.OneStop,
                parity=QSerialInstrument.NoParity,
                flowControl=QSerialInstrument.NoFlowControl,
                eol=b'\r')

    def __init__(self, portname=None, **kwargs):
        args = self.comm | kwargs
        super().__init__(portname, **args)

    def identify(self):
        return 'TEKTRONIX' in self.handshake('*IDN?')


def example():
    from PyQt5.QtCore import QCoreApplication

    app = QCoreApplication([])
    scope = QTDS1000().find()
    print(scope.handshake('*IDN?'))


if __name__ == '__main__':
    example()
