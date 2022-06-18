# QInstrument
PyQt5-compatible framework for controlling scientific instruments

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
PyQt5 applications with the event loop running.
The following script finds a DS345 function generator that
is connected to the computer by a serial cable and pops up
a widget to control that instrument's properties. If no instrument
is found, the widget appears but has all of its controls disabled.

```
from PyQt5.QtWidgets import QApplication
from QInstrument import QDS345Widget
import sys

app = QApplication(sys.argv)
ds345 = QDS345Widget()
ds345.show()
sys.exit(app.exec_())
```

![DS345 Widget](/docs/QDS345Widget.png)

Sometimes a real instrument is not available. For those instances,
`QInstrument` provides "fake" interfaces:

```
from PyQt5.QtWidgets import QApplication
from QInstrument import (QDS345Widget, QFakeDS345)
import sys

app = QApplication(sys.argv)
fake = QFakeDS345()
ds345 = QDS345Widget(device=fake)
ds345.show()
sys.exit(app.exec_())
```
