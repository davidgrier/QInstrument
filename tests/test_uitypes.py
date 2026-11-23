'''The typing modules generated from the .ui files must be current.'''

from pathlib import Path

import pytest

from QInstrument.lib import uitypes

BASE = Path(uitypes.__file__).parents[1]
UIFILES = uitypes.ui_files(BASE)


def test_ui_files_found():
    assert len(UIFILES) >= 7


@pytest.mark.parametrize('ui', UIFILES, ids=lambda p: p.name)
def test_generated_module_is_current(ui):
    out = uitypes.target(ui)
    assert out.exists(), f'run: python -m QInstrument.lib.uitypes ({ui.name})'
    assert out.read_text() == uitypes.generate(ui), (
        f'{out.name} is stale: run python -m QInstrument.lib.uitypes')


def test_generated_children_match_loaded_widget(qtbot):
    '''Every annotated child exists on the widget loaded by uic.'''
    from QInstrument.instruments.Novanta.Opus.widget import QOpusWidget
    from QInstrument.instruments.Novanta.Opus.instrument import QOpus
    ui = BASE / 'instruments/Novanta/Opus/OpusWidget.ui'
    names = [line.split(':')[0].strip()
             for line in uitypes.generate(ui).splitlines()
             if line.startswith('    ') and ': ' in line]
    widget = QOpusWidget(device=QOpus())
    qtbot.addWidget(widget)
    missing = [n for n in names if n not in vars(widget)]
    assert not missing
