import pytest
import sheraf
import tests


@pytest.mark.parametrize("unique", (True, False))
def test_noneok_index(sheraf_connection, unique):
    class ModelSimple(tests.IntAutoModel):
        foo = sheraf.SimpleAttribute().index(noneok=True, unique=unique)
        bar = sheraf.SimpleAttribute().index(noneok=False, unique=unique)

    m = ModelSimple.create(foo=None, bar=None)
    assert m in ModelSimple.search(foo=None)
    assert m not in ModelSimple.search(bar=None)

    n = ModelSimple.create(foo="", bar="")
    assert n in ModelSimple.search(foo="")
    assert n in ModelSimple.search(bar="")

    class ModelInteger(tests.IntAutoModel):
        foo = sheraf.IntegerAttribute().index(noneok=True, unique=unique)
        bar = sheraf.IntegerAttribute().index(noneok=False, unique=unique)

    o = ModelInteger.create(foo=0, bar=0)
    assert o in ModelInteger.search(foo=0)
    assert o in ModelInteger.search(bar=0)


@pytest.mark.parametrize("unique", (True, False))
def test_noneok_index_with_none_as_default(sheraf_connection, unique):
    class ModelSimple(tests.IntAutoModel):
        foo = sheraf.SimpleAttribute(default=None).index(noneok=True, unique=unique)
        bar = sheraf.SimpleAttribute(default=None).index(noneok=False, unique=unique)

    m = ModelSimple.create()
    assert m in ModelSimple.search(foo=None)
    assert m not in ModelSimple.search(bar=None)

    if not unique:
        ModelSimple.create()

    else:
        ModelSimple.create(foo="anything")

        with pytest.raises(sheraf.exceptions.UniqueIndexException):
            ModelSimple.create(bar="anything")


@pytest.mark.parametrize("unique", (True, False))
def test_nullok_index(sheraf_connection, unique):
    class ModelSimple(tests.IntAutoModel):
        foo = sheraf.SimpleAttribute().index(nullok=True, unique=unique)
        bar = sheraf.SimpleAttribute().index(nullok=False, unique=unique)

    m = ModelSimple.create(foo=None, bar=None)
    assert m not in ModelSimple.search(foo=None)
    assert m not in ModelSimple.search(bar=None)
    m.delete()

    n = ModelSimple.create(foo="", bar="")
    assert n in ModelSimple.search(foo="")
    assert n not in ModelSimple.search(bar="")
    n.delete()

    o = ModelSimple.create(foo=0, bar=0)
    assert o in ModelSimple.search(foo=0)
    assert o not in ModelSimple.search(bar=0)
    o.delete()

    p = ModelSimple.create(foo="anything", bar="anything")
    assert p in ModelSimple.search(foo="anything")
    assert p in ModelSimple.search(bar="anything")
    p.delete()
