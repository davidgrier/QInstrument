# QInstrument
PyQt-compatible framework for controlling scientific instruments

## Instruments

### Laser Quantum
- **Opus**: Laser

### PiezoDrive
- **PDUS210**: Piezo transducer driver

### Proscan
- **Proscan II/III**: Microscope stage controller

### Stanford Research Instruments
- **DS345**: 30 MHz Synthesized Function Generator
- **SR830**: 100 kHz Digital Lockin Amplifier

## Interface
All instrument interfaces are intended to be invoked within
PyQt applications. To simplify invocation across platforms
and implementations of PyQt, `QInstrument` leverages the unifying
framework provided by `pyqtgraph`.
The following script finds a DS345 function generator that
is connected to the computer by a serial cable and pops up
a widget to control that instrument's properties. If no instrument
is found, the widget appears but has all of its controls disabled.

```
import pyqtgraph as pg
from QInstrument import QDS345Widget

pg.mkQApp()
ds345 = QDS345Widget()
ds345.show()
pg.exec()
```

<img src="/docs/QDS345Widget.png" width="50%" alt="DS345 Widget">

Sometimes a real instrument is not available. For those instances,
`QInstrument` provides "fake" interfaces:

```
import pyqtgraph as pg
from QInstrument import (QDS345Widget, QFakeDS345)

pg.mkQApp()
fake = QFakeDS345()
ds345 = QDS345Widget(device=fake)
ds345.show()
pg.exec()
```

## Acknowledgements

Work on this project at New York University
is supported by the National Science Foundation of the
United States under award number DMR-2438983.
