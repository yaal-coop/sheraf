import sheraf
from tests import UUIDAutoModel
from sheraf.attributes.index import Index


def test_default_read_and_write_memoization_attribute(sheraf_connection):
    attribute = sheraf.BaseAttribute()
    assert attribute.read_memoization is False
    assert attribute.write_memoization is True


def test_read_and_write_memoization_parameters(sheraf_connection):
    attribute = sheraf.BaseAttribute(read_memoization=True, write_memoization=False)
    assert attribute.read_memoization is True
    assert attribute.write_memoization is False


def test_set_read_memoization_to_true(sheraf_connection):
    sheraf.attributes.base.set_read_memoization(True)
    attribute = sheraf.BaseAttribute()
    assert attribute.read_memoization is True
    sheraf.attributes.base.set_read_memoization(False)


def test_set_write_memoization_to_false(sheraf_connection):
    sheraf.attributes.base.set_write_memoization(False)
    attribute = sheraf.BaseAttribute()
    assert attribute.write_memoization is False
    sheraf.attributes.base.set_write_memoization(True)


def test_attribute_repr():
    class Model(UUIDAutoModel):
        foo = sheraf.SimpleAttribute()

    assert "<SimpleAttribute name=foo>" == repr(Model.attributes["foo"])


def test_index():
    attribute = sheraf.SimpleAttribute()
    primary = Index(attribute, True, "primary", None, None, None, True, True, False)
    unique = Index(attribute, True, "unique", None, None, None, False, True, False)
    multiple = Index(attribute, False, "multiple", None, None, None, False, True, False)

    assert "<Index key=primary unique=True primary>" == repr(primary)
    assert "<Index key=unique unique=True>" == repr(unique)
    assert "<Index key=multiple unique=False>" == repr(multiple)
