import pytest


class InstrumentContractTests:
    '''Shared contract tests for all fake instrument implementations.

    Subclass by setting the following class attributes:

    fake_class : type
        Fake instrument class to instantiate.
    required_properties : set[str]
        All property names that must be registered after construction.
    readonly_properties : set[str]
        Subset of ``required_properties`` whose setters are ``None``.
    roundtrip_cases : list[tuple[str, object]]
        ``(name, value)`` pairs: after ``set(name, value)`` the fake must
        return the same value from ``get(name)``.
    '''

    fake_class = None
    required_properties: set = set()
    readonly_properties: set = set()
    roundtrip_cases: list = []

    @pytest.fixture
    def instrument(self, qtbot):
        return self.fake_class()

    def test_identify_returns_true(self, instrument):
        assert instrument.identify() is True

    def test_is_open(self, instrument):
        assert instrument.isOpen() is True

    def test_required_properties_registered(self, instrument):
        assert self.required_properties.issubset(set(instrument.properties))

    def test_readonly_properties_reject_writes(self, instrument):
        for name in self.readonly_properties:
            before = instrument.get(name)
            instrument.set(name, object())
            assert instrument.get(name) == before, (
                f'read-only property {name!r} changed after set()')

    def test_roundtrip(self, instrument):
        for name, value in self.roundtrip_cases:
            instrument.set(name, value)
            assert instrument.get(name) == value, (
                f'round-trip failed for {name!r}: '
                f'expected {value!r}, got {instrument.get(name)!r}')
