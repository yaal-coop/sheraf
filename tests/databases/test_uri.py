import os

import sheraf

DIR = os.getcwd() + "/"
DEFAULT_ZODBURI_CACHE_SIZE = 5000
DEFAULT_ZODBURI_CACHE_SIZE_BYTES = 0
DEFAULT_ZODBURI_DATABASE_NAME = "unnamed"


def test_default_params_are_zodburi_default_params():
    db = sheraf.Database("zconfig://" + DIR + "tests/zodb_unique_database.conf")
    assert db.name == DEFAULT_ZODBURI_DATABASE_NAME
    assert db.db.database_name == DEFAULT_ZODBURI_DATABASE_NAME
    assert db.db.getCacheSize() == DEFAULT_ZODBURI_CACHE_SIZE
    assert db.db.getCacheSizeBytes() == DEFAULT_ZODBURI_CACHE_SIZE_BYTES
    db.close()


def test_params_override_default_params():
    db = sheraf.Database(
        uri="zconfig://" + DIR + "tests/zodb_unique_database.conf",
        db_args=dict(database_name="toto", cache_size=10, cache_size_bytes=10,),
    )
    assert db.name == "toto"
    assert db.db.database_name == "toto"
    assert db.db.getCacheSize() == 10
    assert db.db.getCacheSizeBytes() == 10
    db.close()


def test_params_override_conf_file():
    db = sheraf.Database(
        uri="zconfig://" + DIR + "tests/zodb_multiple_databases.conf#temp1",
        db_args=dict(database_name="toto", cache_size=10, cache_size_bytes=10,),
    )
    assert db.name == "toto"
    assert db.db.database_name == "toto"
    assert db.db.getCacheSize() == 10
    assert db.db.getCacheSizeBytes() == 10
    db.close()


def test_conf_file_params():
    db = sheraf.Database(
        "zconfig://" + DIR + "tests/zodb_multiple_databases.conf#temp1"
    )
    assert db.name == "database1"
    assert db.db.database_name == "database1"
    assert db.db.getCacheSize() == 7000
    assert db.db.getCacheSizeBytes() == 7000
    db.close()


def test_zconfig_file_for_multiple_db():
    db1 = sheraf.Database(
        "zconfig://" + DIR + "tests/zodb_multiple_databases.conf/#temp1"
    )
    assert db1.name == "database1"
    assert db1.db.database_name == "database1"
    db2 = sheraf.Database(
        "zconfig://" + DIR + "tests/zodb_multiple_databases.conf/#temp2"
    )
    assert db2.name == "database2"
    assert db2.db.database_name == "database2"
    db1.close()
    db2.close()


def test_separation_between_databases():
    db1 = sheraf.Database(
        "zconfig://" + DIR + "tests/zodb_multiple_databases.conf/#temp1"
    )

    class Model1(sheraf.Model):
        table = "table1"

    with sheraf.connection(database_name="database1", commit=True):
        Model1.create()

    db2 = sheraf.Database(
        "zconfig://" + DIR + "tests/zodb_multiple_databases.conf/#temp2"
    )

    class Model2(sheraf.Model):
        table = "table2"

    with sheraf.connection(database_name="database2", commit=True):
        Model2.create()

    with db1.connection() as connection:
        assert "table1" in connection.root()
        assert "table2" not in connection.root()

    with db2.connection() as connection:
        assert "table2" in connection.root()
        assert "table1" not in connection.root()

    db1.close()
    db2.close()
