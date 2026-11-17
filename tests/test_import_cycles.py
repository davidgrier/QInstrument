'''Every package can be the first one that a program imports.

The other tests import ``QInstrument.lib`` early, which can hide a cycle
between packages.  Each module is imported here in an interpreter of its
own, as a script would.
'''
import os
import subprocess
import sys
import unittest

MODULES = (
    'QInstrument',
    'QInstrument.lib',
    'QInstrument.lib.QAbstractInstrument',
    'QInstrument.lib.QSerialInstrument',
    'QInstrument.lib.QInstrumentWidget',
    'QInstrument.widgets',
    'QInstrument.QInstrumentRack',
    'QInstrument.instruments',
    'QInstrument.instruments.StanfordResearch.DS345',
    'QInstrument.instruments.StanfordResearch.SR830',
    'QInstrument.instruments.StanfordResearch.SR844',
    'QInstrument.instruments.IPGPhotonics.IPGLaser',
    'QInstrument.instruments.Novanta.Opus532',
    'QInstrument.instruments.PiezoDrive.PDUS210',
    'QInstrument.instruments.PriorScientific.Proscan',
)


class TestFirstImport(unittest.TestCase):

    def test_each_module_imports_in_a_fresh_interpreter(self):
        env = dict(os.environ, QT_QPA_PLATFORM='offscreen')
        for module in MODULES:
            with self.subTest(module=module):
                result = subprocess.run(
                    [sys.executable, '-I', '-c', f'import {module}'],
                    capture_output=True,
                    text=True,
                    check=False,
                    env=env)
                self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
