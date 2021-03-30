import mock
import pytest

import sheraf
import tests


def test_simple(sheraf_connection):
    class Model(tests.UUIDAutoModel):
        opt = sheraf.SimpleAttribute()

    m = Model.create()
    assert m.opt is None

    m = Model.read(m.id)
    m.opt = mock.sentinel.OPT
    assert mock.sentinel.OPT == m.opt

    m.toto = mock.sentinel.TOTO
    assert mock.sentinel.TOTO == m.toto

    m = Model.read(m.id)
    with pytest.raises(AttributeError):
        m.toto
    assert mock.sentinel.OPT == m.opt

    m.update(opt="YEAH")
    assert "YEAH" == m.opt


def test_string(sheraf_database):
    class M(tests.UUIDAutoModel):
        string = sheraf.StringAttribute()

    with sheraf.connection(commit=True):
        m = M.create()
        assert "" == m.string

    with sheraf.connection():
        m = M.read(m.id)
        assert "" == m.string

    with sheraf.connection(commit=True):
        m = M.create(string=1)
        assert "1" == m.string

    with sheraf.connection():
        m = M.read(m.id)
        assert "1" == m.string

    with sheraf.connection(commit=True):
        m = M.create(string=None)
        assert m.string is None

    with sheraf.connection():
        m = M.read(m.id)
        assert m.string is None


def test_default_value(sheraf_connection):
    class Model(tests.UUIDAutoModel):
        opt_false = sheraf.SimpleAttribute(default=bool)
        opt_true = sheraf.SimpleAttribute(default=True)
        opt_none = sheraf.SimpleAttribute()
        opt_str = sheraf.SimpleAttribute(default=str)
        opt_empty_str = sheraf.SimpleAttribute(default="")

    m = Model.create()
    assert False == m.opt_false
    assert True == m.opt_true
    assert m.opt_none is None
    assert "" == m.opt_str
    assert "" == m.opt_empty_str
    m.opt_empty_str += "a"
    m_bis = Model.create()
    assert "" == m_bis.opt_empty_str


def test_model_default_value(sheraf_connection):
    class M(tests.UUIDAutoModel):
        foo = sheraf.SimpleAttribute(default=lambda m: m.count())

    assert 1 == M.create().foo
    assert 2 == M.create().foo


def test_not_store_deault_value(sheraf_connection):
    class Model(tests.UUIDAutoModel):
        my_attr = sheraf.SimpleAttribute(store_default_value=False)

    model = Model.create()
    model.my_attr
    assert "my_attr" not in model.mapping


def test_define_keyname(sheraf_connection):
    class Model(sheraf.Model):
        table = "model_test_with_simple_attribute_3"
        unique_table_name = False
        opt = sheraf.SimpleAttribute(key="defined_key_in_db")

    m = Model.create()
    m.opt = "data"

    class ModifiedModel(sheraf.Model):
        table = "model_test_with_simple_attribute_3"
        unique_table_name = False
        new_name = sheraf.SimpleAttribute(key="defined_key_in_db")

    m = ModifiedModel.read(m.id)
    assert "data" == m.new_name


def test_inherit_define_keyname(sheraf_connection):
    class ParentModel(sheraf.Model):
        table = "parent_model_test_1"
        unique_table_name = False
        opt = sheraf.SimpleAttribute(key="defined_key_in_db")

    class ChildModel(ParentModel):
        unique_table_name = False
        table = "son_model_test_1"

    m = ChildModel.create()
    m.opt = "data"

    class ModifiedParentModel(sheraf.Model):
        table = "parent_model_test_1"
        unique_table_name = False
        new_name = sheraf.SimpleAttribute(key="defined_key_in_db")

    class ModifiedChildModel(ModifiedParentModel):
        unique_table_name = False
        table = "son_model_test_1"

    m = ModifiedChildModel.read(m.id)
    assert "data" == m.new_name


def test_define_keyname_list(sheraf_connection):
    class Model(sheraf.Model):
        table = "model_test__define_keyname_list"
        a = sheraf.SimpleAttribute(key=("a", "old_a"))
        b = sheraf.SimpleAttribute(key=[0, "b"])

    m = Model.create()
    m.mapping["old_a"] = "a_value"
    m.mapping["b"] = "b_value"

    m = Model.read(m.id)
    assert "a_value" == m.a
    assert "b_value" == m.b

    m = Model.create()
    m.a = 1
    m.b = 2
    assert 1 == m.mapping["a"]
    assert 2 == m.mapping[0]


def test_del(sheraf_connection):
    class Model(tests.UUIDAutoModel):
        attr = sheraf.SimpleAttribute(default="default")

    m = Model.create()
    m.attr = "yolo"
    del m.attr

    assert "attr" not in m.mapping
    assert m.attr == "default"


def test_del_after_read(sheraf_connection):
    class Model(tests.UUIDAutoModel):
        attr = sheraf.SimpleAttribute(default="default")

    m = Model.create()
    m.attr = "yolo"
    m = Model.read(m.id)
    del m.attr

    assert "attr" not in m.mapping
    assert m.attr == "default"


def test_del_on_unsetted_attr(sheraf_connection):
    class Model(tests.UUIDAutoModel):
        attr = sheraf.SimpleAttribute(default="default")

    m = Model.create()
    del m.attr

    assert "attr" not in m.mapping
    assert m.attr == "default"


def test_del_on_specifed_key_attr(sheraf_connection):
    class Model(tests.UUIDAutoModel):
        attr = sheraf.SimpleAttribute(default="default", key="other_key")

    m = Model.create()
    m.attr = "yolo"
    del m.attr

    assert "other_key" not in m.mapping
    assert m.attr == "default"
