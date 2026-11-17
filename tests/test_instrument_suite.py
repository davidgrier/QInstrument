'''Every instrument goes through the path of a user.

An instrument package has a fake, a widget and a tree, and the rack builds
them from the name alone.  This test finds every instrument that the rack
offers (a package with a ``widget.py``) and takes it through that path, so
that a new instrument, or a change to the framework, that breaks one of them
fails here and not at the bench: the fake registers properties that read and
write, the widget binds to the fake and enables itself, the tree builds a
parameter for every property, and the package exports what the rack looks
for.  Nothing here needs hardware.
'''
import importlib

import pytest

from QInstrument.QInstrumentRack import QInstrumentRack

INSTRUMENTS = sorted(QInstrumentRack._instrumentPaths())
IDS = [name for _, name in INSTRUMENTS]


def load(package: tuple[str, str], module: str):
    '''Return the class that the module *module* of an instrument exports.'''
    manufacturer, name = package
    mod = importlib.import_module(
        f'QInstrument.instruments.{manufacturer}.{name}.{module}')
    return getattr(mod, mod.__all__[0])


@pytest.fixture(params=INSTRUMENTS, ids=IDS)
def package(request):
    '''Return ``(manufacturer, name)`` of one instrument.'''
    return request.param


@pytest.fixture
def fake(package, qtbot):
    return load(package, 'fake')()


class TestFake:

    def test_the_fake_is_open_and_identifies(self, fake):
        assert fake.isOpen()
        assert fake.identify() is True

    def test_the_fake_registers_properties(self, fake):
        assert fake.properties

    def test_every_getter_runs(self, fake):
        '''A getter may return ``None`` (no limit is active), not raise.'''
        for name in fake.properties:
            fake._properties[name]['getter']()

    def test_a_property_keeps_the_value_it_is_given(self, fake):
        '''Writing back what was read changes nothing and raises nothing.'''
        changed = []
        for name in fake.properties:
            if fake._properties[name]['setter'] is None:
                continue
            before = fake.get(name)
            meta = fake.propertyMeta(name)
            if before is None or not (meta.get('minimum', before) <= before
                                      <= meta.get('maximum', before)):
                continue
            fake.set(name, before)
            if fake.get(name) != before:
                changed.append(name)
        assert changed == []

    def test_the_settings_round_trip(self, fake):
        '''Applying the settings is idempotent: the second time changes
        nothing, even if the first clamped a value to the range.'''
        settings = fake.settings
        assert settings
        fake.settings = settings
        applied = fake.settings
        fake.settings = applied
        assert fake.settings == applied


class TestWidget:

    @pytest.fixture
    def widget(self, package, fake, qtbot):
        widget = load(package, 'widget')(device=fake)
        qtbot.addWidget(widget)
        return widget

    def test_the_widget_binds_to_the_fake(self, widget, fake):
        assert widget.device is fake
        assert widget.isEnabled()

    def test_the_widget_manages_properties_of_the_device(self, widget, fake):
        assert widget.properties
        assert set(widget.properties) <= set(fake.properties)

    def test_the_widget_reads_the_values_of_the_device(self, widget, fake):
        settings = widget.settings
        assert set(settings) == set(widget.properties)

    def test_the_widget_declares_its_instrument(self, package):
        cls = load(package, 'widget')
        assert cls.INSTRUMENT is not None or cls.FAKEDEVICE is not None


class TestTree:

    @pytest.fixture
    def tree(self, package, fake, qtbot):
        pytest.importorskip('pyqtgraph')
        tree = load(package, 'tree')(device=fake)
        qtbot.addWidget(tree)
        return tree

    def test_the_tree_binds_to_the_fake(self, tree, fake):
        assert tree.device is fake

    def test_the_tree_has_a_parameter_for_every_property(self, tree, fake):
        missing = [name for name in fake.properties
                   if name not in tree._params]
        assert missing == []


class TestPackage:

    def test_the_package_exports_its_classes(self, package):
        manufacturer, name = package
        mod = importlib.import_module(
            f'QInstrument.instruments.{manufacturer}.{name}')
        assert len(mod.__all__) == 3
        for exported in mod.__all__:
            assert getattr(mod, exported) is not None

    def test_the_rack_can_find_the_widget_module(self, package):
        _, name = package
        assert QInstrumentRack._findInstrumentModule(name) is not None
