from QInstrument.lib.QSerialInstrument import QSerialInstrument


class QTDS1000(QSerialInstrument):

    comm = dict(baudRate=QSerialInstrument.Baud9600,
                dataBits=QSerialInstrument.Data8,
                stopBits=QSerialInstrument.OneStop,
                parity=QSerialInstrument.NoParity,
                flowControl=QSerialInstrument.HardwareControl,
                eol='\n')

    def __init__(self, portName=None, **kwargs):
        args = self.comm | kwargs
        super().__init__(portName, **args)

    def identify(self):
        return 'TEK' in self.handshake('*IDN?')

    def clear(self):
        self.sendbreak()
        return 'DCL' in self.receive()
