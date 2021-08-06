from PyQt5.QtCore import (pyqtSlot, pyqtSignal)
from PyQt5.QtSerialPort import (QSerialPort, QSerialPortInfo)
import logging

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)


class SerialInstrument(QSerialPort):

    def __init__(self, portName=None, eol='', **kwargs):
        super().__init__(**kwargs)
        self.eol = eol
        self.open(portName)

    def open(self, portName):
        if portName is None:
            return
        self.setPortName(portName)
        if super().open(QSerialPort.ReadWrite):
            self.clear()
            if not self.identify():
                logger.warning(f'Device on {portName} did not identify as expected')
                self.close()
        else:
            logger.warning(f'Could not open {portName}')

    def find(self):
        names = [port.portName() for port in QSerialPortInfo.availablePorts()]
        for name in names:
            self.open(name)
            if self.isOpen():
                return self
        logger.error('Could not find device')
        return None
    
    def send(self, data):
        if type(data) == str:
            cmd = data + self.eol
            self.write(bytes(cmd, 'utf-8'))
        else:
            self.write(data)
        self.flush()
        logger.debug(f' sent: {data}')

    def receive(self):
        self.waitForReadyRead(1000)
        response = self.readAll()
        while (self.waitForReadyRead(100)):
            response.append(self.readAll())
        logger.debug(f' received: {response}')
        return response.data().decode('utf-8')

    def handshake(self, cmd):
        self.send(cmd)
        return self.receive()

    def identify(self):
        return True

    def get_value(self, query, dtype=float):
        return dtype(self.handshake(query).strip())

    @pyqtSlot(object)
    def set_value(self, value):
        name = str(self.sender().objectName())
        if hasattr(self, name):
            setattr(self, name, value)
        else:
            logger.warning(f'Failed to set {name} ({value}): Not a valid property')
