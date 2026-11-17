import numpy as np
import pytest
from unittest.mock import patch
from instruments.Tektronix.TDS1000.instrument import QTDS1000

#: What the oscilloscope reports about the waveform (SI units).
PREAMBLE = {
    'WFMPRE:YOFF?': 128.,
    'WFMPRE:XINCR?': 1e-3,
    'HOR:POS?': 0.5,
    'WFMPRE:YMULT?': 0.1,
    'WFMPRE:YZERO?': 0.25,
}


def block(samples: bytes, digits: int = 4) -> bytes:
    '''An IEEE 488.2 definite-length block followed by the terminator.'''
    length = f'{len(samples):0{digits}d}'.encode()
    return b'#' + str(digits).encode() + length + samples + b'\n'


class Stream:
    '''Stands for the serial port: serves bytes to readn(), as it does.'''

    def __init__(self, data: bytes) -> None:
        self.data = data

    def __call__(self, n: int = 1) -> bytes:
        chunk, self.data = self.data[:n], self.data[n:]
        return chunk


@pytest.fixture
def scope(qtbot):
    return QTDS1000()


@pytest.fixture
def sent(scope):
    '''Record what the instrument transmits, and answer the preamble.'''
    log: list[str] = []
    with patch.object(scope, 'transmit', side_effect=log.append), \
            patch.object(scope, 'getValue',
                         side_effect=lambda q: PREAMBLE[q]):
        yield log


class TestIdentify:

    def test_accepts_a_tektronix(self, scope):
        with patch.object(scope, 'handshake',
                          return_value='TEKTRONIX,TDS 1012,0,CF:91'):
            assert scope.identify() is True

    def test_rejects_another_maker(self, scope):
        with patch.object(scope, 'handshake', return_value='ACME,1,2,3'):
            assert scope.identify() is False


class TestReadBlock:

    def test_returns_the_declared_data(self, scope):
        with patch.object(scope, 'readn', Stream(block(b'abcdef', 2))):
            assert scope._readBlock() == b'abcdef'

    def test_a_sample_equal_to_the_terminator_is_data(self, scope):
        samples = bytes([1, 10, 3, 10, 5])           # 10 is a newline
        with patch.object(scope, 'readn', Stream(block(samples))):
            assert scope._readBlock() == samples

    def test_consumes_the_terminator(self, scope):
        stream = Stream(block(b'xy') + b'NEXT')
        with patch.object(scope, 'readn', stream):
            scope._readBlock()
        assert stream.data == b'NEXT'

    def test_rejects_a_response_that_is_not_a_block(self, scope):
        with patch.object(scope, 'readn', Stream(b'ERROR\n')):
            with pytest.raises(ValueError):
                scope._readBlock()

    def test_a_short_block_times_out(self, scope):
        stream = Stream(b'#4' + b'0010' + b'abc')    # declares 10, has 3
        with patch.object(scope, 'readn', stream):
            with pytest.raises(TimeoutError):
                scope._readBlock()


class TestData:

    def test_configures_the_waveform_transfer(self, scope, sent):
        with patch.object(scope, 'readn', Stream(block(b'\x80\x80'))):
            scope.data('CH2')
        assert sent == ['DATA:SOURCE CH2', 'DATA:WIDTH 1', 'DATA:ENC RPB',
                        'CURVE?']

    def test_converts_samples_to_volts(self, scope, sent):
        samples = bytes([128, 138, 118, 10])
        with patch.object(scope, 'readn', Stream(block(samples))):
            t, v = scope.data()
        # volts = YMULT * (sample - YOFF) + YZERO
        assert np.allclose(v, [0.25, 1.25, -0.75, -11.55])

    def test_the_time_axis_is_centered_on_the_horizontal_position(
            self, scope, sent):
        with patch.object(scope, 'readn', Stream(block(bytes(100)))):
            t, v = scope.data()
        assert len(t) == len(v) == 100
        assert np.allclose(np.diff(t), 1e-3)
        assert t[50] == pytest.approx(0.5)

    def test_a_missing_scale_factor_is_an_error(self, scope):
        with patch.object(scope, 'transmit'), \
                patch.object(scope, 'getValue', return_value=None):
            with pytest.raises(ValueError):
                scope.data()
