import sheraf


class MyAutoModel(sheraf.AutoModel):
    my_attribute = sheraf.SimpleAttribute()


def test_create_default_auto(sheraf_database):
    assert "myautomodel" == MyAutoModel.table

    with sheraf.connection(commit=True):
        m = MyAutoModel.create()
        assert "myautomodel" == m.table

    with sheraf.connection() as conn:
        assert m == MyAutoModel.read(m.id)
        assert "myautomodel" == m.table
        assert "myautomodel" in conn.root()


class MyIntAutoModel(sheraf.IntAutoModel):
    my_attribute = sheraf.SimpleAttribute()


def test_create_default_intauto(sheraf_database):
    assert "myintautomodel" == MyIntAutoModel.table

    with sheraf.connection(commit=True):
        assert 0 == MyIntAutoModel.count()
        m = MyIntAutoModel.create()
        assert "myintautomodel" == m.table
        assert 0 == m.id
        assert 1 == MyIntAutoModel.count()
        assert 1 == MyIntAutoModel.create().id

    with sheraf.connection() as conn:
        assert m == MyIntAutoModel.read(m.id)
        assert "myintautomodel" == m.table
        assert "myintautomodel" in conn.root()
