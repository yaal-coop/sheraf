import codecs

import legacycrypt
import pytest
import sheraf
import tests


class PasswordModelA(tests.UUIDAutoModel):
    pwd = sheraf.PasswordAttribute()


class PasswordModelB(tests.UUIDAutoModel):
    pwd = sheraf.PasswordAttribute(method=legacycrypt.METHOD_SHA256)


class Rot13PasswordAttribute(sheraf.PasswordAttribute):
    @staticmethod
    def crypt(clear, *args, **kwargs):
        return codecs.encode(clear, "rot_13")

    @staticmethod
    def compare(clear, crypted):
        return codecs.encode(clear, "rot_13") == crypted


class PasswordModelC(tests.UUIDAutoModel):
    pwd = Rot13PasswordAttribute()


@pytest.mark.parametrize("Model", [PasswordModelA, PasswordModelB, PasswordModelC])
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
