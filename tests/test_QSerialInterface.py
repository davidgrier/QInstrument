import logging
import pytest
from unittest.mock import patch, MagicMock

import lib.QSerialInterface as module
from lib.QSerialInterface import QSerialInterface


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def iface(qtbot):
    '''QSerialInterface with no port opened, newline EOL.'''
    return QSerialInterface(eol='\n')


@pytest.fixture
def iface_crlf(qtbot):
    '''QSerialInterface with no port opened, CRLF EOL.'''
    return QSerialInterface(eol='\r\n')


@pytest.fixture
def iface_fast(qtbot):
    '''QSerialInterface with 1 ms timeout for timeout tests.'''
    return QSerialInterface(eol='\n', timeout=1)


# ---------------------------------------------------------------------------
# Initialization
# ---------------------------------------------------------------------------

class TestInitialization:

    def test_eol_str_encoded(self, qtbot):
        iface = QSerialInterface(eol='\n')
        assert iface.eol == b'\n'

    def test_eol_bytes_unchanged(self, qtbot):
        iface = QSerialInterface(eol=b'\r\n')
        assert iface.eol == b'\r\n'

    def test_timeout_default(self, qtbot):
        iface = QSerialInterface()
        assert iface.timeout == 100

    def test_timeout_explicit(self, qtbot):
        iface = QSerialInterface(timeout=500)
        assert iface.timeout == 500

    def test_blocking_default_true(self, qtbot):
        iface = QSerialInterface()
        assert iface.blocking is True

    def test_not_open_on_construction(self, qtbot):
        iface = QSerialInterface()
        assert not iface.isOpen()


# ---------------------------------------------------------------------------
# blocking property
# ---------------------------------------------------------------------------

class TestBlocking:

    def test_set_false(self, iface):
        iface.blocking = False
        assert iface.blocking is False

    def test_set_true_after_false(self, iface):
        iface.blocking = False
        iface.blocking = True
        assert iface.blocking is True

    def test_set_true_when_already_true_does_not_raise(self, iface):
        iface.blocking = True  # readyRead was never connected
        assert iface.blocking is True


# ---------------------------------------------------------------------------
# transmit
# ---------------------------------------------------------------------------

class TestTransmit:

    @patch.object(QSerialInterface, 'isOpen', return_value=True)
    @patch.object(QSerialInterface, 'write')
    @patch.object(QSerialInterface, 'flush')
    def test_str_encoded_and_eol_appended(
            self, mock_flush, mock_write, mock_open, iface):
        iface.transmit('FREQ?')
        mock_write.assert_called_once_with(b'FREQ?\n')
        mock_flush.assert_called_once()

    @patch.object(QSerialInterface, 'isOpen', return_value=True)
    @patch.object(QSerialInterface, 'write')
    @patch.object(QSerialInterface, 'flush')
    def test_bytes_passed_through_without_eol(
            self, mock_flush, mock_write, mock_open, iface):
        iface.transmit(b'\x01\x02\x03')
        mock_write.assert_called_once_with(b'\x01\x02\x03')

    @patch.object(QSerialInterface, 'isOpen', return_value=False)
    def test_closed_logs_warning(self, mock_open, iface, caplog):
        with caplog.at_level(logging.WARNING):
            iface.transmit('FREQ?')
        assert 'not open' in caplog.text

    @patch.object(QSerialInterface, 'isOpen', return_value=False)
    @patch.object(QSerialInterface, 'write')
    def test_closed_does_not_write(self, mock_write, mock_open, iface):
        iface.transmit('FREQ?')
        mock_write.assert_not_called()


# ---------------------------------------------------------------------------
# receive
# ---------------------------------------------------------------------------

class TestReceive:

    @patch.object(QSerialInterface, 'bytesAvailable', return_value=True)
    @patch.object(QSerialInterface, 'readAll', return_value=b'HELLO\n')
    def test_strips_eol(self, mock_read, mock_avail, iface):
        assert iface.receive() == 'HELLO'

    @patch.object(QSerialInterface, 'bytesAvailable', return_value=True)
    @patch.object(QSerialInterface, 'readAll', return_value=b'HELLO\r\n')
    def test_multibyte_eol_stripped(self, mock_read, mock_avail, iface_crlf):
        assert iface_crlf.receive() == 'HELLO'

    @patch.object(QSerialInterface, 'bytesAvailable', return_value=True)
    @patch.object(QSerialInterface, 'readAll', return_value=b'HELLO\n')
    def test_raw_returns_bytes(self, mock_read, mock_avail, iface):
        assert iface.receive(raw=True) == b'HELLO'

    @patch.object(QSerialInterface, 'bytesAvailable', return_value=False)
    def test_timeout_returns_empty_string(self, mock_avail, iface_fast):
        assert iface_fast.receive() == ''

    @patch.object(QSerialInterface, 'bytesAvailable', return_value=False)
    def test_timeout_logs(self, mock_avail, iface_fast, caplog):
        with caplog.at_level(logging.DEBUG):
            iface_fast.receive()
        assert 'Timeout' in caplog.text

    @patch.object(QSerialInterface, 'bytesAvailable', return_value=True)
    @patch.object(QSerialInterface, 'readAll', return_value=b'DATA\r')
    def test_override_eol(self, mock_read, mock_avail, iface):
        assert iface.receive(eol='\r') == 'DATA'

    @patch.object(QSerialInterface, 'bytesAvailable', return_value=True)
    @patch.object(QSerialInterface, 'readAll', return_value=b'DATA\r')
    def test_override_eol_as_bytes(self, mock_read, mock_avail, iface):
        assert iface.receive(eol=b'\r') == 'DATA'

    @patch.object(QSerialInterface, 'bytesAvailable', return_value=True)
    @patch.object(QSerialInterface, 'readAll', return_value=b'A\nB\nC')
    def test_returns_up_to_first_eol(self, mock_read, mock_avail, iface):
        assert iface.receive() == 'A'


# ---------------------------------------------------------------------------
# readn
# ---------------------------------------------------------------------------

class TestReadn:

    @patch.object(QSerialInterface, 'isOpen', return_value=True)
    @patch.object(QSerialInterface, 'bytesAvailable', return_value=True)
    @patch.object(QSerialInterface, 'readAll', return_value=b'ABCDE')
    def test_trims_to_n(self, mock_read, mock_avail, mock_open, iface):
        assert iface.readn(3) == b'ABC'

    @patch.object(QSerialInterface, 'isOpen', return_value=True)
    @patch.object(QSerialInterface, 'bytesAvailable', return_value=True)
    @patch.object(QSerialInterface, 'readAll', return_value=b'AB')
    def test_exact_match(self, mock_read, mock_avail, mock_open, iface):
        assert iface.readn(2) == b'AB'

    @patch.object(QSerialInterface, 'isOpen', return_value=True)
    @patch.object(QSerialInterface, 'bytesAvailable',
                  side_effect=[True, False, False])
    @patch.object(QSerialInterface, 'readAll', return_value=b'AB')
    def test_timeout_returns_partial(
            self, mock_read, mock_avail, mock_open, iface_fast, caplog):
        with caplog.at_level(logging.WARNING):
            result = iface_fast.readn(5)
        assert result == b'AB'
        assert 'Timeout' in caplog.text

    @patch.object(QSerialInterface, 'isOpen', return_value=False)
    def test_closed_returns_empty(self, mock_open, iface):
        assert iface.readn(3) == b''


# ---------------------------------------------------------------------------
# _handleReadyRead
# ---------------------------------------------------------------------------

class TestHandleReadyRead:

    @patch.object(QSerialInterface, 'readAll', return_value=b'DATA\n')
    def test_emits_data_ready(self, mock_read, iface, qtbot):
        with qtbot.waitSignal(iface.dataReady, timeout=1000) as blocker:
            iface._handleReadyRead()
        assert blocker.args == ['DATA']

    @patch.object(QSerialInterface, 'readAll', return_value=b'HELLO\n')
    def test_emitted_value_has_no_eol(self, mock_read, iface, qtbot):
        with qtbot.waitSignal(iface.dataReady, timeout=1000) as blocker:
            iface._handleReadyRead()
        assert '\n' not in blocker.args[0]

    @patch.object(QSerialInterface, 'readAll', return_value=b'PARTIAL')
    def test_no_emit_without_eol(self, mock_read, iface, qtbot):
        with qtbot.assertNotEmitted(iface.dataReady):
            iface._handleReadyRead()

    @patch.object(QSerialInterface, 'readAll', return_value=b'LINE1\nLINE2')
    def test_remainder_retained_in_buffer(self, mock_read, iface, qtbot):
        with qtbot.waitSignal(iface.dataReady, timeout=1000):
            iface._handleReadyRead()
        assert bytes(iface._buffer) == b'LINE2'

    @patch.object(QSerialInterface, 'readAll', return_value=b'LINE1\n')
    def test_buffer_cleared_when_no_remainder(self, mock_read, iface, qtbot):
        with qtbot.waitSignal(iface.dataReady, timeout=1000):
            iface._handleReadyRead()
        assert iface._buffer.isEmpty()

    @patch.object(QSerialInterface, 'readAll', return_value=b'DATA\r\n')
    def test_multibyte_eol_no_remainder(self, mock_read, iface_crlf, qtbot):
        with qtbot.waitSignal(iface_crlf.dataReady, timeout=1000) as blocker:
            iface_crlf._handleReadyRead()
        assert blocker.args == ['DATA']
        assert iface_crlf._buffer.isEmpty()

    @patch.object(QSerialInterface, 'readAll', return_value=b'DATA\r\nEXTRA')
    def test_multibyte_eol_with_remainder(self, mock_read, iface_crlf, qtbot):
        with qtbot.waitSignal(iface_crlf.dataReady, timeout=1000) as blocker:
            iface_crlf._handleReadyRead()
        assert blocker.args == ['DATA']
        assert bytes(iface_crlf._buffer) == b'EXTRA'

    @patch.object(QSerialInterface, 'readAll', side_effect=[b'LI', b'NE\n'])
    def test_accumulates_across_multiple_reads(self, mock_read, iface, qtbot):
        with qtbot.assertNotEmitted(iface.dataReady):
            iface._handleReadyRead()
        with qtbot.waitSignal(iface.dataReady, timeout=1000) as blocker:
            iface._handleReadyRead()
        assert blocker.args == ['LINE']


# ---------------------------------------------------------------------------
# open
# ---------------------------------------------------------------------------

class TestOpen:

    def test_none_port_returns_false(self, iface):
        assert iface.open(None) is False
