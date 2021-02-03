import sheraf
import tests


def test_string_indexation_nullok_by_default(sheraf_connection):
    class Model(tests.UUIDAutoModel):
        attr = sheraf.StringAttribute().index()

    m = Model.create(attr="yolo")
    assert m in Model.search(attr="yolo")

    n = Model.create(attr=None)
    assert n not in Model.search(attr=None)

    o = Model.create(attr="")
    assert o not in Model.search(attr="")
