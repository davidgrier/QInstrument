from __future__ import annotations

import logging
from qtpy import QtCore
from QInstrument.lib.QSerialInstrument import QSerialInstrument

logger = logging.getLogger(__name__)


class QProscan(QSerialInstrument):
    '''Prior Scientific Proscan II/III Microscope Stage Controller.

    Controls the XY stage and Z focus drive of a Prior Scientific
    motorized microscope stage over RS-232.

    Signals
    -------
    positionChanged(list[int])
        Emitted by :meth:`position` with the current ``[x, y, z]``
        coordinates in micrometers.

    Properties
    ==========
    speed : int
        Maximum XY stage speed. Range [1, 100].
    acceleration : int
        XY stage acceleration. Range [1, 100].
    scurve : int
        Time derivative of XY stage acceleration. Range [1, 100].
    stepsize : float
        XY single-step size [um].
    zspeed : int
        Maximum focus drive speed. Range [1, 100].
    zacceleration : int
        Focus drive acceleration. Range [1, 100].
    zscurve : int
        Time derivative of focus acceleration. Range [1, 100].
    zstepsize : float
        Focus drive single-step size [um].
    resolution : float
        Stage encoder resolution [um/step].
    flip : bool
        True: invert Y axis direction.
    mirror : bool
        True: invert X axis direction.
    moving : bool
        True if the stage or focus drive is currently in motion.
        Read-only.
    '''

    positionChanged = QtCore.Signal(object)

    comm = dict(baudRate=QSerialInstrument.BaudRate.Baud9600,
                dataBits=QSerialInstrument.DataBits.Data8,
                stopBits=QSerialInstrument.StopBits.OneStop,
                parity=QSerialInstrument.Parity.NoParity,
                flowControl=QSerialInstrument.FlowControl.NoFlowControl,
                eol='\r')

    def __init__(self, portName: str | None = None, **kwargs) -> None:
        super().__init__(portName, **(self.comm | kwargs))
        self._flip: bool = False
        self._mirror: bool = False
        self._registerProperties()

    def _registerProperties(self) -> None:
        for name, cmd in (('speed',         'SMS'),
                          ('acceleration',  'SAS'),
                          ('scurve',        'SCS'),
                          ('zspeed',        'SMZ'),
                          ('zacceleration', 'SAZ'),
                          ('zscurve',       'SCZ')):
            self.registerProperty(
                name,
                getter=lambda c=cmd: self.getValue(c, int),
                setter=lambda v, c=cmd: self.expect(f'{c},{int(v)}', '0'),
                ptype=int)
        self.registerProperty(
            'stepsize',
            getter=lambda: float(self.handshake('X').split(',')[0]),
            setter=lambda v: self.expect(f'X,{float(v)},{float(v)}', '0'),
            ptype=float)
        self.registerProperty(
            'zstepsize',
            getter=lambda: self.getValue('C', float),
            setter=lambda v: self.expect(f'C,{float(v)}', '0'),
            ptype=float)
        self.registerProperty(
            'resolution',
            getter=lambda: self.getValue('RES,s', float),
            setter=lambda v: self.transmit(f'RES,s,{float(v)}'),
            ptype=float)
        self.registerProperty(
            'flip',
            getter=lambda: self._flip,
            setter=self._set_flip,
            ptype=bool)
        self.registerProperty(
            'mirror',
            getter=lambda: self._mirror,
            setter=self._set_mirror,
            ptype=bool)
        self.registerProperty(
            'moving',
            getter=lambda: bool(self.status() & 0xF),
            setter=None,
            ptype=bool)

    def identify(self) -> bool:
        '''Return True if the VERSION response is a 3-character string.

        A valid Proscan controller returns a 3-character firmware
        version string (e.g. ``'1.2'``).
        '''
        return len(self.version()) == 3

    def version(self) -> str:
        '''Return the 3-character firmware version string.'''
        return self.handshake('VERSION')

    def position(self) -> list[int]:
        '''Return the current stage position and emit :attr:`positionChanged`.

        Returns
        -------
        list[int]
            ``[x, y, z]`` coordinates of the current stage position
            in micrometers.
        '''
        pos = list(map(int, self.handshake('P').split(',')))
        self.positionChanged.emit(pos)
        return pos

    def set_position(self, position: list[int]) -> bool:
        '''Define the coordinates of the current physical position.

        Parameters
        ----------
        position : list[int]
            ``[x, y]`` or ``[x, y, z]`` coordinates to assign to the
            current stage position, in micrometers.

        Returns
        -------
        bool
            True if the controller acknowledged the command.
        '''
        coords = ','.join(map(str, position))
        return self.expect(f'P,{coords}', '0')

    @QtCore.Slot()
    def set_origin(self) -> bool:
        '''Set the coordinate system origin to the current position.

        Returns
        -------
        bool
            True if the controller acknowledged the command.
        '''
        return self.expect('Z', '0')

    def move_to(self, position: list[int],
                relative: bool = False) -> bool:
        '''Move the stage to a target position.

        Parameters
        ----------
        position : list[int]
            ``[x, y]`` target coordinates in micrometers.
        relative : bool
            True: move by ``position`` relative to current location.
            False: move to the absolute coordinates. Default: False.

        Returns
        -------
        bool
            True once the controller acknowledges the motion command.
        '''
        cmd = 'GR' if relative else 'G'
        coords = ','.join(map(str, position))
        return self.expect(f'{cmd},{coords}', 'R')

    def move_to_origin(self) -> bool:
        '''Move the stage to the coordinate origin.

        Returns
        -------
        bool
            True once the controller acknowledges the motion command.
        '''
        return self.expect('M', 'R')

    @QtCore.Slot(object)
    def set_velocity(self, velocity: list[float]) -> None:
        '''Start continuous stage motion at the specified velocity.

        Passing ``[0, 0]`` stops motion. Velocity is maintained until
        a new :meth:`set_velocity` or :meth:`stop` call.

        Parameters
        ----------
        velocity : list[float]
            ``[vx, vy]`` velocity components in micrometers per second.
        '''
        v = ','.join(map(str, velocity))
        self.expect(f'VS,{v}', 'R')

    @QtCore.Slot()
    def stop(self) -> bool:
        '''Stop all stage and focus motion immediately.

        Returns
        -------
        bool
            True once the controller acknowledges the stop command.
        '''
        return self.expect('I', 'R')

    def status(self) -> int:
        '''Return the raw controller status word.

        Returns
        -------
        int
            Bitmask; bits 0–3 indicate motion in progress.
        '''
        return self.getValue('$', int)

    def stepLeft(self) -> bool:
        '''Step the stage one increment in the −X direction.'''
        return self.expect('L', 'R')

    def stepRight(self) -> bool:
        '''Step the stage one increment in the +X direction.'''
        return self.expect('R', 'R')

    def stepForward(self) -> bool:
        '''Step the stage one increment in the +Y direction.'''
        return self.expect('F', 'R')

    def stepBackward(self) -> bool:
        '''Step the stage one increment in the −Y direction.'''
        return self.expect('B', 'R')

    def stepUp(self) -> bool:
        '''Step the focus drive one increment upward.'''
        return self.expect('U', 'R')

    def stepDown(self) -> bool:
        '''Step the focus drive one increment downward.'''
        return self.expect('D', 'R')

    def description(self) -> list[str]:
        '''Return lines of hardware description from the controller.'''
        return self._read_lines('?')

    def stage(self) -> list[str]:
        '''Return lines of stage description from the controller.'''
        return self._read_lines('STAGE')

    def focus(self) -> list[str]:
        '''Return lines of focus system description from the controller.'''
        return self._read_lines('FOCUS')

    def _read_lines(self, query: str) -> list[str]:
        '''Transmit ``query`` and collect response lines until ``END``.

        Parameters
        ----------
        query : str
            Command string to send to the controller.

        Returns
        -------
        list[str]
            Response lines, including the terminating ``END`` line.
        '''
        self.transmit(query)
        lines = []
        while True:
            line = self.receive()
            lines.append(line)
            if 'END' in line:
                break
        return lines

    def _set_flip(self, value: bool) -> None:
        self._flip = bool(value)
        self.expect(f'YD,{-1 if value else 1}', '0')

    def _set_mirror(self, value: bool) -> None:
        self._mirror = bool(value)
        self.expect(f'XD,{-1 if value else 1}', '0')


def example() -> None:
    proscan = QProscan().find()
    if proscan is not None:
        print(f'version: {proscan.version()}')
        print(f'position: {proscan.position()}')
        proscan.close()


__all__ = ['QProscan']


if __name__ == '__main__':
    example()
