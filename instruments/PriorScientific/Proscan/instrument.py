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
        coordinates in µm.

    Properties
    ==========
    speed : int
        Maximum XY stage speed. Range [1, 100].
    acceleration : int
        XY stage acceleration. Range [1, 100].
    scurve : int
        Time derivative of XY stage acceleration. Range [1, 100].
    stepsize : float
        XY single-step size [µm].
    zspeed : int
        Maximum focus drive speed. Range [1, 100].
    zacceleration : int
        Focus drive acceleration. Range [1, 100].
    zscurve : int
        Time derivative of focus acceleration. Range [1, 100].
    zstepsize : float
        Focus drive single-step size [µm].
    xresolution : float
        X-axis encoder resolution [µm/step]. Read-only.
    yresolution : float
        Y-axis encoder resolution [µm/step]. Read-only.
    zresolution : float
        Z-axis encoder resolution [µm/step]. Read-only.
    upr : float
        XY stage µm per revolution [µm/rev].
    zupr : float
        Z focus drive µm per revolution [µm/rev].
    flip : bool
        True: invert Y axis direction.
    mirror : bool
        True: invert X axis direction.
    moving : bool
        True if the stage or focus drive is currently in motion.
        Read-only.
    limits : tuple[bool, bool, bool, bool] or None
        Active limit switches per axis ``(x, y, z, fourth)``, or
        ``None`` if no limits are currently active. Read-only.

    Limit Switch Bits
    -----------------

    Both ``=`` (triggered since last read) and ``LMT`` (currently active)
    return a one-byte hex value.  Each bit identifies one limit switch:

    +------+------+-------+
    | Bit  | Mask | Limit |
    +======+======+=======+
    | D00  | 0x01 | +X    |
    +------+------+-------+
    | D01  | 0x02 | −X    |
    +------+------+-------+
    | D02  | 0x04 | +Y    |
    +------+------+-------+
    | D03  | 0x08 | −Y    |
    +------+------+-------+
    | D04  | 0x10 | +Z    |
    +------+------+-------+
    | D05  | 0x20 | −Z    |
    +------+------+-------+
    | D06  | 0x40 | +4th  |
    +------+------+-------+
    | D07  | 0x80 | −4th  |
    +------+------+-------+

    RS-232 Commands
    ---------------

    +---------+---------+----------+------------------------------------------+
    | Command | Args    | Response | Description                              |
    +=========+=========+==========+==========================================+
    | ?       |         | ...,END  | Hardware description                     |
    |         |         |          | (multi-line, ends with END)              |
    +---------+---------+----------+------------------------------------------+
    | $       |         | int      | Motion status bitmask                    |
    |         |         |          | (bits 0-3: motion active)                |
    +---------+---------+----------+------------------------------------------+
    | =       |         | hex      | Limit switches triggered since last read |
    +---------+---------+----------+------------------------------------------+
    | LMT     |         | hex      | Currently active limit switches          |
    +---------+---------+----------+------------------------------------------+
    | I       |         | R        | Controlled stop (decelerate to halt)     |
    +---------+---------+----------+------------------------------------------+
    | K       |         | R        | Emergency stop (immediate halt)          |
    +---------+---------+----------+------------------------------------------+
    | VERSION |         | str      | Firmware version string                  |
    +---------+---------+----------+------------------------------------------+
    | SERIAL  |         | str      | Controller serial number                 |
    +---------+---------+----------+------------------------------------------+
    | COMP    | mode    | 0        | Communication mode (0 = standard)        |
    +---------+---------+----------+------------------------------------------+
    | P       |         | x,y,z    | Query current stage position [µm]        |
    +---------+---------+----------+------------------------------------------+
    | P       | x,y[,z] | 0        | Define current position label [µm]       |
    +---------+---------+----------+------------------------------------------+
    | Z       |         | 0        | Zero: set coordinate origin at           |
    |         |         |          | current position                         |
    +---------+---------+----------+------------------------------------------+
    | G       | x,y[,z] | R        | Absolute move to position [µm]           |
    +---------+---------+----------+------------------------------------------+
    | GR      | x,y[,z] | R        | Relative move by offset [µm]             |
    +---------+---------+----------+------------------------------------------+
    | GX      | x       | R        | Move X axis to absolute position [µm]    |
    +---------+---------+----------+------------------------------------------+
    | GY      | y       | R        | Move Y axis to absolute position [µm]    |
    +---------+---------+----------+------------------------------------------+
    | GZ      | z       | R        | Move Z (focus) to absolute position [µm] |
    +---------+---------+----------+------------------------------------------+
    | M       |         | R        | Move to origin (coordinate zero)         |
    +---------+---------+----------+------------------------------------------+
    | VS      | vx,vy   | R        | Continuous XY velocity [µm/s];           |
    |         |         |          | VS,0,0 to stop                           |
    +---------+---------+----------+------------------------------------------+
    | VZ      | vz      | R        | Continuous Z velocity [µm/s];            |
    |         |         |          | VZ,0 to stop                             |
    +---------+---------+----------+------------------------------------------+
    | H       |         | R        | Home stage to hardware limits            |
    +---------+---------+----------+------------------------------------------+
    | L       |         | R        | Step one increment in −X direction       |
    +---------+---------+----------+------------------------------------------+
    | R       |         | R        | Step one increment in +X direction       |
    +---------+---------+----------+------------------------------------------+
    | F       |         | R        | Step one increment in +Y direction       |
    +---------+---------+----------+------------------------------------------+
    | B       |         | R        | Step one increment in −Y direction       |
    +---------+---------+----------+------------------------------------------+
    | U       |         | R        | Step focus drive one increment upward    |
    +---------+---------+----------+------------------------------------------+
    | D       |         | R        | Step focus drive one increment downward  |
    +---------+---------+----------+------------------------------------------+
    | X       |         | sx,sy    | Query XY step sizes [µm]                 |
    +---------+---------+----------+------------------------------------------+
    | X       | sx,sy   | 0        | Set XY step sizes [µm]                   |
    +---------+---------+----------+------------------------------------------+
    | C       |         | sz       | Query Z step size [µm]                   |
    +---------+---------+----------+------------------------------------------+
    | C       | sz      | 0        | Set Z step size [µm]                     |
    +---------+---------+----------+------------------------------------------+
    | XD      | ±1      | 0        | Set X-axis direction                     |
    |         |         |          | (+1 normal, −1 inverted)                 |
    +---------+---------+----------+------------------------------------------+
    | YD      | ±1      | 0        | Set Y-axis direction                     |
    |         |         |          | (+1 normal, −1 inverted)                 |
    +---------+---------+----------+------------------------------------------+
    | SMS     | [n]     | int/0    | Get/set XY max speed [1–100]             |
    +---------+---------+----------+------------------------------------------+
    | SAS     | [n]     | int/0    | Get/set XY acceleration [1–100]          |
    +---------+---------+----------+------------------------------------------+
    | SCS     | [n]     | int/0    | Get/set XY S-curve factor [1–100]        |
    +---------+---------+----------+------------------------------------------+
    | SMZ     | [n]     | int/0    | Get/set Z max speed [1–100]              |
    +---------+---------+----------+------------------------------------------+
    | SAZ     | [n]     | int/0    | Get/set Z acceleration [1–100]           |
    +---------+---------+----------+------------------------------------------+
    | SCZ     | [n]     | int/0    | Get/set Z S-curve factor [1–100]         |
    +---------+---------+----------+------------------------------------------+
    | RES,X   |         | float    | Query X-axis encoder resolution          |
    |         |         |          | [µm/step]                                |
    +---------+---------+----------+------------------------------------------+
    | RES,Y   |         | float    | Query Y-axis encoder resolution          |
    |         |         |          | [µm/step]                                |
    +---------+---------+----------+------------------------------------------+
    | RES,Z   |         | float    | Query Z-axis encoder resolution          |
    |         |         |          | [µm/step]                                |
    +---------+---------+----------+------------------------------------------+
    | UPR     | [v]     | float/0  | Get/set XY µm per revolution [µm/rev]    |
    +---------+---------+----------+------------------------------------------+
    | ZUPR    | [v]     | float/0  | Get/set Z µm per revolution [µm/rev]     |
    +---------+---------+----------+------------------------------------------+
    | J       | n       | 0        | Joystick enable (1) / disable (0)        |
    +---------+---------+----------+------------------------------------------+
    | JXD     | ±1      | 0        | Joystick X direction                     |
    |         |         |          | (+1 normal, −1 inverted)                 |
    +---------+---------+----------+------------------------------------------+
    | JYD     | ±1      | 0        | Joystick Y direction                     |
    |         |         |          | (+1 normal, −1 inverted)                 |
    +---------+---------+----------+------------------------------------------+
    | JZD     | ±1      | 0        | Joystick Z direction                     |
    |         |         |          | (+1 normal, −1 inverted)                 |
    +---------+---------+----------+------------------------------------------+
    | STAGE   |         | ...,END  | Stage description                        |
    |         |         |          | (multi-line, ends with END)              |
    +---------+---------+----------+------------------------------------------+
    | FOCUS   |         | ...,END  | Focus system description                 |
    |         |         |          | (multi-line, ends with END)              |
    +---------+---------+----------+------------------------------------------+
    '''

    positionChanged = QtCore.Signal(object)

    comm = dict(baudRate=QSerialInstrument.BaudRate.Baud9600,
                dataBits=QSerialInstrument.DataBits.Data8,
                stopBits=QSerialInstrument.StopBits.OneStop,
                parity=QSerialInstrument.Parity.NoParity,
                flowControl=QSerialInstrument.FlowControl.NoFlowControl,
                eol='\r')

    def _registerProperties(self) -> None:
        self._flip: bool = False
        self._mirror: bool = False
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
        for name, axis in (('xresolution', 'X'),
                            ('yresolution', 'Y'),
                            ('zresolution', 'Z')):
            self.registerProperty(
                name,
                getter=lambda a=axis: self.getValue(f'RES,{a}', float),
                setter=None,
                ptype=float)
        self.registerProperty(
            'upr',
            getter=lambda: self.getValue('UPR', float),
            setter=lambda v: self.expect(f'UPR,{float(v)}', '0'),
            ptype=float)
        self.registerProperty(
            'zupr',
            getter=lambda: self.getValue('ZUPR', float),
            setter=lambda v: self.expect(f'ZUPR,{float(v)}', '0'),
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
        self.registerProperty(
            'limits',
            getter=lambda: self.active_limits(),
            setter=None,
            ptype=object)

    def receive(self, **kwargs) -> str:
        '''Return the next response line, handling E18 queue-full errors.

        If the controller returns ``E18`` (command queue full), logs a
        warning and returns an empty string so that all callers treat
        the response as a failed read.

        Returns
        -------
        str
            Response string, or ``''`` on timeout or E18.
        '''
        response = super().receive(**kwargs)
        if response == 'E18':
            logger.warning('controller queue full (E18)')
            return ''
        return response

    def identify(self) -> bool:
        '''Return True if the device responds to ``COMP,0`` with ``'0'``.

        Sets the controller to standard communication mode as a side
        effect, ensuring a known state for all subsequent commands.

        Returns
        -------
        bool
            True if the controller acknowledges ``COMP,0``.
        '''
        return self.expect('COMP,0', '0')

    def version(self) -> str:
        '''Return the 3-character firmware version string.'''
        return self.handshake('VERSION')

    def position(self) -> list[int]:
        '''Return the current stage position and emit :attr:`positionChanged`.

        Returns
        -------
        list[int]
            ``[x, y, z]`` coordinates of the current stage position
            in µm.
        '''
        pos = list(map(int, self.handshake('P').split(',')))
        self.positionChanged.emit(pos)
        return pos

    def set_position(self, position: list[int]) -> bool:
        '''Define the coordinates of the current physical position.

        No axis may be moving when this command is issued.  Returns
        ``False`` immediately if the stage is in motion.

        Parameters
        ----------
        position : list[int]
            ``[x, y]`` or ``[x, y, z]`` coordinates to assign to the
            current stage position, in µm.

        Returns
        -------
        bool
            True if the controller acknowledged the command.
        '''
        if self.status() & 0xF:
            logger.warning('set_position() called while stage is moving')
            return False
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
            ``[x, y]`` target coordinates in µm.
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
            ``[vx, vy]`` velocity components in µm/s.
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

    @QtCore.Slot()
    def emergency_stop(self) -> bool:
        '''Stop all stage and focus motion immediately without deceleration.

        Sends the ``K`` command (hard stop).  Prefer :meth:`stop` for
        normal halts; use this only when immediate cessation is required.

        Returns
        -------
        bool
            True if the controller acknowledged the command.
        '''
        return self.expect('K', 'R')

    def triggered_limits(self) -> tuple[bool, bool, bool, bool] | None:
        '''Return per-axis limit switches triggered since the last read.

        Reads the ``=`` register, which clears automatically on read.
        Returns ``None`` if no limits were triggered, so callers can use
        a simple truthiness check.

        Returns
        -------
        tuple[bool, bool, bool, bool] or None
            ``(x, y, z, fourth)`` — ``True`` on each axis that had a
            limit triggered since the previous call; ``None`` if none.
        '''
        return self._parse_limits(int(self.handshake('='), 16))

    def active_limits(self) -> tuple[bool, bool, bool, bool] | None:
        '''Return per-axis limit switches currently in contact.

        Returns ``None`` if no limits are active, so callers can use a
        simple truthiness check.

        Returns
        -------
        tuple[bool, bool, bool, bool] or None
            ``(x, y, z, fourth)`` — ``True`` on each axis whose limit
            switch is currently active; ``None`` if none.
        '''
        return self._parse_limits(int(self.handshake('LMT'), 16))

    def _parse_limits(self, raw: int) -> tuple[bool, bool, bool, bool] | None:
        if raw == 0:
            return None
        return (bool(raw & 0x03), bool(raw & 0x0C),
                bool(raw & 0x30), bool(raw & 0xC0))

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

    def _read_lines(self, query: str, max_lines: int = 32) -> list[str]:
        '''Transmit ``query`` and collect response lines until ``END``.

        Parameters
        ----------
        query : str
            Command string to send to the controller.
        max_lines : int
            Maximum number of lines to read before giving up.
            Prevents an infinite loop if the controller stalls or
            never sends ``END``.  Default: 32.

        Returns
        -------
        list[str]
            Response lines, including the terminating ``END`` line,
            or a partial list if the read timed out or hit ``max_lines``.
        '''
        self.transmit(query)
        lines = []
        for _ in range(max_lines):
            line = self.receive()
            if not line:
                break
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
