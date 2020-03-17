import sheraf


def test_create_int_model(sheraf_database):
    class MyIntModel(sheraf.models.IntIndexedNamedAttributesModel):
        table = "my_int_model"
        my_attribute = sheraf.SimpleAttribute()

    with sheraf.connection(commit=True):
        m = MyIntModel.create()

    with sheraf.connection():
        assert m == MyIntModel.read(m.id)


def test_create_ordered_intmodel(sheraf_database):
    class MyIntModel(sheraf.models.IntOrderedNamedAttributesModel):
        table = "my_ordered_int_model"
        my_attribute = sheraf.SimpleAttribute()

    with sheraf.connection(commit=True):
        m0 = MyIntModel.create()
        assert m0.id == 0
        m1 = MyIntModel.create()
        assert m1.id == 1

    with sheraf.connection():
        assert m0 == MyIntModel.read(0)
        assert m1 == MyIntModel.read(1)
