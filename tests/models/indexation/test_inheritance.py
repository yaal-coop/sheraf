import sheraf
import tests


def test_inheritance_indexation(sheraf_connection):
    class A(tests.IntAutoModel):
        foo = sheraf.SimpleAttribute()
        aindex = sheraf.Index("foo")

    class B(A):
        bindex = sheraf.Index("foo")

    b = B.create(foo="foo")
    assert b in B.search(aindex="foo")
    assert b in B.search(bindex="foo")
