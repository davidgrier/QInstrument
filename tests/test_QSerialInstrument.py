import logging
import pytest
from unittest.mock import patch, MagicMock
from qtpy.QtSerialPort import QSerialPortInfo
from lib.QSerialInstrument import QSerialInstrument


class AlwaysIdentifies(QSerialInstrument):
    '''Concrete instrument whose identify() always returns True.'''
    def identify(self) -> bool:
        return True


class NeverIdentifies(QSerialInstrument):
    '''Concrete instrument whose identify() always returns False.'''
    def identify(self) -> bool:
        return False


@pytest.fixture
def inst(qtbot):
    return AlwaysIdentifies()


def _mock_port(name: str) -> MagicMock:
    port = MagicMock(spec=QSerialPortInfo)
    port.portName.return_value = name
    return port


# ---------------------------------------------------------------------------
# open()
# ---------------------------------------------------------------------------

class TestOpen:

    def test_returns_false_when_interface_fails_to_open(self, inst):
        with patch.object(inst._interface, 'open', return_value=False):
            assert inst.open('ttyUSB0') is False

    def test_returns_true_when_port_opens_and_identify_passes(self, inst):
        with patch.object(inst._interface, 'open', return_value=True), \
             patch.object(inst._interface, 'isOpen', return_value=True):
            assert inst.open('ttyUSB0') is True

    def test_identify_not_called_when_interface_open_fails(self, inst):
        with patch.object(inst._interface, 'open', return_value=False), \
             patch.object(inst, 'identify') as mock_identify:
            inst.open('ttyUSB0')
        mock_identify.assert_not_called()

    def test_closes_port_when_identify_fails(self, qtbot):
        dev = NeverIdentifies()
        with patch.object(dev._interface, 'open', return_value=True), \
             patch.object(dev._interface, 'close') as mock_close, \
             patch.object(dev._interface, 'isOpen', return_value=False):
            dev.open('ttyUSB0')
        mock_close.assert_called_once()

    def test_returns_false_when_identify_fails(self, qtbot):
        dev = NeverIdentifies()
        with patch.object(dev._interface, 'open', return_value=True), \
             patch.object(dev._interface, 'isOpen', return_value=False):
            assert dev.open('ttyUSB0') is False

    def test_logs_when_identify_fails(self, qtbot, caplog):
        dev = NeverIdentifies()
        with patch.object(dev._interface, 'open', return_value=True), \
             patch.object(dev._interface, 'isOpen', return_value=False), \
             caplog.at_level(logging.DEBUG):
            dev.open('ttyUSB0')
        assert 'NeverIdentifies' in caplog.text


# ---------------------------------------------------------------------------
# find()
# ---------------------------------------------------------------------------

class TestFind:

    def test_always_returns_self(self, inst):
        with patch('lib.QSerialInstrument.QSerialPortInfo') as mock_info:
            mock_info.availablePorts.return_value = []
            assert inst.find() is inst

    def test_stops_after_first_successful_open(self, inst):
        with patch('lib.QSerialInstrument.QSerialPortInfo') as mock_info, \
             patch.object(inst._interface, 'open', return_value=True) as mock_open, \
             patch.object(inst._interface, 'isOpen', return_value=True):
            mock_info.availablePorts.return_value = [
                _mock_port('ttyUSB0'), _mock_port('ttyUSB1')]
            inst.find()
            mock_open.assert_called_once_with('ttyUSB0')

    def test_tries_subsequent_ports_when_earlier_fail(self, qtbot):
        dev = AlwaysIdentifies()
        with patch('lib.QSerialInstrument.QSerialPortInfo') as mock_info, \
             patch.object(dev._interface, 'open', side_effect=[False, True]) as mock_open, \
             patch.object(dev._interface, 'isOpen', return_value=True):
            mock_info.availablePorts.return_value = [
                _mock_port('ttyUSB0'), _mock_port('ttyUSB1')]
            dev.find()
            assert mock_open.call_count == 2

    def test_logs_error_when_no_port_matches(self, inst, caplog):
        with patch('lib.QSerialInstrument.QSerialPortInfo') as mock_info, \
             patch.object(inst._interface, 'open', return_value=False), \
             caplog.at_level(logging.ERROR):
            mock_info.availablePorts.return_value = [_mock_port('ttyS0')]
            inst.find()
        assert 'AlwaysIdentifies' in caplog.text


# ---------------------------------------------------------------------------
# Delegation — transmit / receive / isOpen / close
# ---------------------------------------------------------------------------

class TestDelegation:

    def test_transmit_delegates_to_interface(self, inst):
        with patch.object(inst._interface, 'transmit') as mock_tx:
            inst.transmit('CMD')
        mock_tx.assert_called_once_with('CMD')

    def test_receive_delegates_to_interface(self, inst):
        with patch.object(inst._interface, 'receive', return_value='RESP'):
            assert inst.receive() == 'RESP'

    def test_isOpen_delegates_to_interface(self, inst):
        with patch.object(inst._interface, 'isOpen', return_value=True):
            assert inst.isOpen() is True

    def test_close_delegates_to_interface(self, inst):
        with patch.object(inst._interface, 'close') as mock_close:
            inst.close()
        mock_close.assert_called_once()
