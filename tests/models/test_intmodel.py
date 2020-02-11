import sheraf


class TestIntModel:
    class MyIntModel(sheraf.models.IntIndexedNamedAttributesModel):
        table = "my_int_model"
        my_attribute = sheraf.SimpleAttribute()

    def test_create(self, sheraf_database):
        with sheraf.connection(commit=True):
            m = self.MyIntModel.create()

        with sheraf.connection():
            assert m == self.MyIntModel.read(m.id)


class TestOrderedIntModel:
    class MyIntModel(sheraf.models.IntOrderedNamedAttributesModel):
        table = "my_ordered_int_model"
        my_attribute = sheraf.SimpleAttribute()

    def test_create(self, sheraf_database):
        with sheraf.connection(commit=True):
            m0 = self.MyIntModel.create()
            assert m0.id == 0
            m1 = self.MyIntModel.create()
            assert m1.id == 1

        with sheraf.connection():
            assert m0 == self.MyIntModel.read(0)
            assert m1 == self.MyIntModel.read(1)
