import crypt
import pytest
import tests
import sheraf


class PasswordModelA(tests.UUIDAutoModel):
    pwd = sheraf.PasswordAttribute()


class PasswordModelB(tests.UUIDAutoModel):
    pwd = sheraf.PasswordAttribute(method=crypt.METHOD_SHA256)


@pytest.mark.parametrize("Model", [PasswordModelA, PasswordModelB])
def test_password(sheraf_connection, Model):
    m = Model.create()

    assert m.pwd is None

    m.pwd = "yeah"

    assert m.pwd == "yeah"
    assert not (m.pwd != "yeah")
    assert "yeah" == m.pwd
    assert not ("yeah" != m.pwd)

    assert m.mapping["pwd"] != "yeah"
    assert str(m.pwd) != "yeah"
    assert not (str(m.pwd) == "yeah")

    m.pwd = None
    assert m.pwd is None
