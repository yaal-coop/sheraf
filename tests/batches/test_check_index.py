import re

import sheraf
from sheraf.batches.checks import check_health, print_health

from . import fixture1


def test_healthcheck_attributes_index_when_instance_deleted(sheraf_database, capsys):
    from .fixture1 import Model2unique

    with sheraf.connection(commit=True) as conn:
        Model2unique.create(simple="simple1", str_indexed="str1")
        Model2unique.create(simple="simple1", str_indexed="str2")
        m = Model2unique.create(simple="simple2", str_indexed="str3")
        mmapping = sheraf.types.SmallDict(m.mapping)
        m.delete()
        index_table = conn.root()["model2unique_table"]["str_indexed"]
        index_table["str3"] = mmapping

    with sheraf.connection() as conn:
        kwargs = dict(model_checks=["index"], instance_checks=[], attribute_checks=[])

        assert "str1" in conn.root()["model2unique_table"]["str_indexed"]
        assert "str2" in conn.root()["model2unique_table"]["str_indexed"]
        health = check_health(fixture1, **kwargs)["check_model_index"]

        assert {"str_indexed": {"ok": 2, "ko": 1}} == health[
            "tests.batches.fixture1.Model2unique"
        ]

        print_health(fixture1, **kwargs)
        stdout = capsys.readouterr().out
        assert re.search(r"tests.batches.fixture1.Model2unique[^\n]*1[^\n]*2", stdout)


def test_healthcheck_attributes_index_with_key_when_instance_deleted(
    sheraf_database, capsys
):
    from .fixture1 import Model2kunique

    with sheraf.connection(commit=True) as conn:
        Model2kunique.create(simple="simple1", str_indexed="str1")
        Model2kunique.create(simple="simple1", str_indexed="str2")
        m = Model2kunique.create(simple="simple2", str_indexed="str3")
        mmapping = sheraf.types.SmallDict(m.mapping)
        m.delete()
        index_table = conn.root()["model2kunique_table"]["str"]
        index_table["str3"] = mmapping

    with sheraf.connection() as conn:
        kwargs = dict(model_checks=["index"], instance_checks=[], attribute_checks=[])

        assert "str1" in conn.root()["model2kunique_table"]["str"]
        assert "str2" in conn.root()["model2kunique_table"]["str"]
        health = check_health(fixture1, **kwargs)["check_model_index"]

        assert {"str": {"ok": 2, "ko": 1}} == health[
            "tests.batches.fixture1.Model2kunique"
        ]


def test_multiple_healthcheck_attributes_index_when_instance_deleted(
    sheraf_database, capsys
):
    from .fixture1 import Model2

    with sheraf.connection(commit=True) as conn:
        Model2.create(simple="simple1", str_indexed="str1")
        index_table = conn.root()["model2_table"]["str_indexed"]
        m21 = Model2.create(simple="simple21", str_indexed="str2")
        m22 = Model2.create(simple="simple22", str_indexed="str2")
        m21_deletedmapping = sheraf.types.SmallDict(m21.mapping)
        assert index_table["str2"] == [m21.mapping, m22.mapping]
        m21.delete()
        index_table["str2"] = [m21_deletedmapping, m22.mapping]

    with sheraf.connection() as conn:
        kwargs = dict(model_checks=["index"], instance_checks=[], attribute_checks=[])

        assert "str1" in conn.root()["model2_table"]["str_indexed"]
        assert "str2" in conn.root()["model2_table"]["str_indexed"]
        health = check_health(fixture1, **kwargs)["check_model_index"]

        assert {"str_indexed": {"ok": 1, "ko": 1}} == health[
            "tests.batches.fixture1.Model2"
        ]


def test_multiple_healthcheck_attributes_index_with_key_when_instance_deleted(
    sheraf_database, capsys
):
    from .fixture1 import Model2k

    with sheraf.connection(commit=True) as conn:
        Model2k.create(simple="simple1", str_indexed="str1")
        index_table = conn.root()["model2k_table"]["str"]
        m21 = Model2k.create(simple="simple21", str_indexed="str2")
        m22 = Model2k.create(simple="simple22", str_indexed="str2")
        m21_deletedmapping = sheraf.types.SmallDict(m21.mapping)
        assert index_table["str2"] == [m21.mapping, m22.mapping]
        m21.delete()
        index_table["str2"] = [m21_deletedmapping, m22.mapping]

    with sheraf.connection() as conn:
        kwargs = dict(model_checks=["index"], instance_checks=[], attribute_checks=[])

        assert "str1" in conn.root()["model2k_table"]["str"]
        assert "str2" in conn.root()["model2k_table"]["str"]
        health = check_health(fixture1, **kwargs)["check_model_index"]

        assert {"str": {"ok": 1, "ko": 1}} == health["tests.batches.fixture1.Model2k"]


def test_multiple_healthcheck_attributes_index(sheraf_database, capsys):
    from .fixture1 import Model2

    with sheraf.connection(commit=True) as conn:
        Model2.create(simple="simple1", str_indexed="str1")
        Model2.create(simple="simple2", str_indexed="str2")
        index_table = conn.root()["model2_table"]["str_indexed"]
        del index_table["str1"]

    with sheraf.connection() as conn:
        kwargs = dict(instance_checks=[], attribute_checks=["index"])

        assert "str1" not in conn.root()["model2_table"]["str_indexed"]
        assert "str2" in conn.root()["model2_table"]["str_indexed"]
        health = check_health(fixture1, **kwargs)["check_attributes_index"]

        assert {"str_indexed": {"ok": 1, "ko": 1}} == health[
            "tests.batches.fixture1.Model2"
        ]

        print_health(fixture1, **kwargs)
        stdout = capsys.readouterr().out
        assert re.search(r"tests.batches.fixture1.Model2[^\n]*1[^\n]*1", stdout)


def test_multiple_healthcheck_attributes_index_with_key(sheraf_database, capsys):
    from .fixture1 import Model2k

    with sheraf.connection(commit=True) as conn:
        Model2k.create(simple="simple1", str_indexed="str1")
        Model2k.create(simple="simple2", str_indexed="str2")
        index_table = conn.root()["model2k_table"]["str"]
        del index_table["str1"]

    with sheraf.connection() as conn:
        kwargs = dict(instance_checks=[], attribute_checks=["index"])

        assert "str1" not in conn.root()["model2k_table"]["str"]
        assert "str2" in conn.root()["model2k_table"]["str"]
        health = check_health(fixture1, **kwargs)["check_attributes_index"]

        assert {"str": {"ok": 1, "ko": 1}} == health["tests.batches.fixture1.Model2k"]

        print_health(fixture1, **kwargs)
        stdout = capsys.readouterr().out
        assert re.search(r"tests.batches.fixture1.Model2k[^\n]*1[^\n]*1", stdout)


def test_healthcheck_attributes_index(sheraf_database, capsys):
    from .fixture1 import Model2unique

    with sheraf.connection(commit=True) as conn:
        Model2unique.create(simple="simple1", str_indexed="str1")
        Model2unique.create(simple="simple2", str_indexed="str2")
        index_table = conn.root()["model2unique_table"]["str_indexed"]
        del index_table["str1"]

    with sheraf.connection() as conn:
        kwargs = dict(instance_checks=[], attribute_checks=["index"])

        assert "str1" not in conn.root()["model2unique_table"]["str_indexed"]
        assert "str2" in conn.root()["model2unique_table"]["str_indexed"]
        health = check_health(fixture1, **kwargs)["check_attributes_index"]

        assert {"str_indexed": {"ok": 1, "ko": 1}} == health[
            "tests.batches.fixture1.Model2unique"
        ]

        print_health(fixture1, **kwargs)
        stdout = capsys.readouterr().out
        assert re.search(r"tests.batches.fixture1.Model2unique[^\n]*1[^\n]*1", stdout)


def test_healthcheck_attributes_index_with_key(sheraf_database, capsys):
    from .fixture1 import Model2kunique

    with sheraf.connection(commit=True) as conn:
        Model2kunique.create(simple="simple1", str_indexed="str1")
        Model2kunique.create(simple="simple2", str_indexed="str2")
        index_table = conn.root()["model2kunique_table"]["str"]
        del index_table["str1"]

    with sheraf.connection() as conn:
        kwargs = dict(instance_checks=[], attribute_checks=["index"])

        assert "str1" not in conn.root()["model2kunique_table"]["str"]
        assert "str2" in conn.root()["model2kunique_table"]["str"]
        health = check_health(fixture1, **kwargs)["check_attributes_index"]

        assert {"str": {"ok": 1, "ko": 1}} == health[
            "tests.batches.fixture1.Model2kunique"
        ]

        print_health(fixture1, **kwargs)
        stdout = capsys.readouterr().out
        assert re.search(r"tests.batches.fixture1.Model2kunique[^\n]*1[^\n]*1", stdout)


def test_healthcheck_attributes_index_non_primitive(sheraf_database, capsys):
    from .fixture1 import Model3, DummyModel

    with sheraf.connection(commit=True) as conn:
        Model3.create(simple="simple1", obj_indexed=DummyModel.create(v="str1"))
        Model3.create(simple="simple2", obj_indexed=DummyModel.create(v="str2"))
        index_table = conn.root()["model3_table"]["obj_indexed"]
        del index_table["str1"]

    with sheraf.connection() as conn:
        assert "str1" not in conn.root()["model3_table"]["obj_indexed"]
        assert "str2" in conn.root()["model3_table"]["obj_indexed"]

        health = check_health(fixture1, instance_checks=[], attribute_checks=["index"])[
            "check_attributes_index"
        ]

        assert {"obj_indexed": {"ok": 1, "ko": 1}} == health[
            "tests.batches.fixture1.Model3"
        ]

        print_health(fixture1)
        stdout = capsys.readouterr().out
        assert re.search(r"tests.batches.fixture1.Model3[^\n]*1[^\n]*1", stdout)


def test_healthcheck_attributes_index_non_primitive_with_key(sheraf_database, capsys):
    from .fixture1 import Model3k, DummyModel

    with sheraf.connection(commit=True) as conn:
        Model3k.create(simple="simple1", obj_indexed=DummyModel.create(v="str1"))
        Model3k.create(simple="simple2", obj_indexed=DummyModel.create(v="str2"))

        index_table = conn.root()["model3k_table"]["obj"]
        del index_table["str1"]

    with sheraf.connection() as conn:
        assert "str1" not in conn.root()["model3k_table"]["obj"]
        assert "str2" in conn.root()["model3k_table"]["obj"]

        health = check_health(fixture1, instance_checks=[], attribute_checks=["index"])[
            "check_attributes_index"
        ]

        assert {"obj": {"ok": 1, "ko": 1}} == health["tests.batches.fixture1.Model3k"]

        print_health(fixture1)
        stdout = capsys.readouterr().out
        assert re.search(r"tests.batches.fixture1.Model3k[^\n]*1[^\n]*1", stdout)


def test_index_table_not_yet_created(sheraf_database, capsys):
    class Cowboy(sheraf.Model):
        table = "future_cowboys"
        name = sheraf.StringAttribute()

    with sheraf.connection(commit=True):
        Cowboy.create(name="George")
        Cowboy.create(name="Peter")

    class Cowboy(sheraf.Model):
        table = "future_cowboys"
        name = sheraf.StringAttribute().index()

    with sheraf.connection():
        health = check_health(Cowboy, attribute_checks=["index"])

    assert {"ok": 0, "ko": 2} == health["check_attributes_index"][
        "tests.batches.test_check_index.Cowboy"
    ]["name"]
