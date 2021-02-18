import sheraf
from tests import UUIDAutoModel
from sheraf.attributes.index import Index


def test_default_read_and_write_memoization_attribute(sheraf_connection):
    attribute = sheraf.Attribute()
    assert attribute.read_memoization is False
    assert attribute.write_memoization is True


def test_read_and_write_memoization_parameters(sheraf_connection):
    attribute = sheraf.Attribute(read_memoization=True, write_memoization=False)
    assert attribute.read_memoization is True
    assert attribute.write_memoization is False


def test_set_read_memoization_to_true(sheraf_connection):
    sheraf.attributes.set_read_memoization(True)
    attribute = sheraf.Attribute()
    assert attribute.read_memoization is True
    sheraf.attributes.set_read_memoization(False)


def test_set_write_memoization_to_false(sheraf_connection):
    sheraf.attributes.set_write_memoization(False)
    attribute = sheraf.Attribute()
    assert attribute.write_memoization is False
    sheraf.attributes.set_write_memoization(True)


def test_attribute_repr():
    class Model(UUIDAutoModel):
        foo = sheraf.SimpleAttribute()

    assert "<SimpleAttribute name=foo>" == repr(Model.attributes["foo"])


def test_index():
    attribute = sheraf.SimpleAttribute()
    primary = Index(attribute, key="primary", primary=True)
    unique = Index(attribute, key="unique", unique=True)
    multiple = Index(attribute, key="multiple", unique=False)

    assert "<Index key=primary unique=True primary>" == repr(primary)
    assert "<Index key=unique unique=True>" == repr(unique)
    assert "<Index key=multiple unique=False>" == repr(multiple)
