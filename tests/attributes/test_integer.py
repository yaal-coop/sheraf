import sheraf
import tests


def test_integer(sheraf_connection):
    class Model(tests.UUIDAutoModel):
        attr = sheraf.IntegerAttribute()

    m = Model.create(attr=1)
    assert 1 == m.attr

    m.attr = "2"
    assert 2 == m.attr

    m.assign(attr=3)
    assert 3 == m.attr

    m.assign(attr="4")
    assert 4 == m.attr


def test_indexed_integer(sheraf_connection):
    class Model(tests.UUIDAutoModel):
        attr = sheraf.IntegerAttribute().index()

    m = Model.create(attr=1)
    assert m in Model.search(attr=1)

    m.attr = "2"
    assert m in Model.search(attr=2)

    m.assign(attr=3)
    assert m in Model.search(attr=3)

    m.assign(attr="4")
    assert m in Model.search(attr=4)
