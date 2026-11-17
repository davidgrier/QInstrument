'''The package list in pyproject.toml is the list of the packages.

setuptools puts into the wheel only the packages that are listed, so a
package that is missing from the list works in a checkout and is absent
from what ``pip install`` installs.  Adding an instrument means adding its
package to the list; this test says when that was forgotten.
'''
import unittest
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10
    import tomli as tomllib

ROOT = Path(__file__).resolve().parent.parent
NOT_PACKAGES = ('tests', 'docs', 'build', 'dist')


def configuration() -> dict:
    with open(ROOT / 'pyproject.toml', 'rb') as f:
        return tomllib.load(f)['tool']['setuptools']


def package_directories() -> set[str]:
    '''Return the dotted names of the directories that have __init__.py.'''
    found = set()
    for path in ROOT.rglob('__init__.py'):
        relative = path.parent.relative_to(ROOT).parts
        if relative and (relative[0] in NOT_PACKAGES
                         or relative[0].startswith('.')
                         or relative[0].endswith('.egg-info')):
            continue
        found.add('.'.join(('QInstrument',) + relative))
    return found


class TestPackaging(unittest.TestCase):

    def test_every_package_is_listed(self):
        listed = set(configuration()['packages'])
        self.assertEqual(
            sorted(package_directories() - listed),
            [],
            'packages that are not in pyproject.toml, and so not in the '
            'wheel')

    def test_every_listed_package_exists(self):
        listed = set(configuration()['packages'])
        self.assertEqual(
            sorted(listed - package_directories()),
            [],
            'packages in pyproject.toml that have no directory')

    def test_the_packages_are_taken_from_the_root_of_the_repository(self):
        self.assertEqual(configuration()['package-dir'],
                         {'QInstrument': '.'})

    def test_every_ui_file_is_in_the_wheel(self):
        data = configuration()['package-data']['QInstrument']
        self.assertIn('**/*.ui', data)
        self.assertTrue(list(ROOT.glob('instruments/*/*/*.ui')))


if __name__ == '__main__':
    unittest.main()
