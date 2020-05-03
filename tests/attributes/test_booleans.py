import mock
import pytest
import sheraf
import tests


def test_boolean(sheraf_connection):
    class ModelForTest(tests.UUIDAutoModel):
        opt = sheraf.BooleanAttribute()

    m = ModelForTest.create()
    assert m.opt is False

    m = ModelForTest.read(m.id)
    m.opt = True
    assert m.opt is True

    m.toto = mock.sentinel.TOTO
    assert mock.sentinel.TOTO == m.toto

    m = ModelForTest.read(m.id)
    with pytest.raises(AttributeError):
        m.toto
    assert m.opt is True


def test_int_casting(sheraf_database):
    class Model(tests.UUIDAutoModel):
        opt = sheraf.BooleanAttribute()

    with sheraf.connection(commit=True):
        mtrue = Model.create(opt=1)
        mfalse = Model.create(opt=0)

        assert mtrue.opt is True
        assert mfalse.opt is False

    with sheraf.connection():
        mtrue = Model.read(mtrue.id)
        mfalse = Model.read(mfalse.id)

        assert mtrue.opt is True
        assert mfalse.opt is False


def test_True_is_settable(sheraf_connection):
    class ModelForTest(tests.UUIDAutoModel):
        opt = sheraf.BooleanAttribute(default=True)

    m = ModelForTest.create()
    assert m.opt is True
