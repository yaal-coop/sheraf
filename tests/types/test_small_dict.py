import pytest
import sheraf
import ZODB


@pytest.mark.parametrize(
    "database",
    [
        pytest.lazy_fixture("sheraf_database"),
        pytest.lazy_fixture("sheraf_zeo_database"),
        #    pytest.lazy_fixture("sheraf_pgsql_relstorage_database"),
    ],
)
def test_empty_dict_no_conflict(database):
    database.nestable = True

    with sheraf.connection(commit=True) as conn:
        conn.root()["mydict"] = sheraf.types.SmallDict()

    with sheraf.connection(commit=True) as conn1:
        conn1.root()["mydict"]._p_changed = True

        with sheraf.connection(commit=True) as conn2:
            conn2.root()["mydict"]._p_changed = True


@pytest.mark.parametrize(
    "database",
    [
        pytest.lazy_fixture("sheraf_database"),
        pytest.lazy_fixture("sheraf_zeo_database"),
        #    pytest.lazy_fixture("sheraf_pgsql_relstorage_database"),
    ],
)
def test_same_item_same_modification_no_conflict(database):
    database.nestable = True

    with sheraf.connection(commit=True) as conn:
        conn.root()["mydict"] = sheraf.types.SmallDict({"something": None})

    with sheraf.connection(commit=True) as conn1:

        with sheraf.connection(commit=True) as conn2:
            conn2.root()["mydict"]["something"] = "YOLO"

        conn1.root()["mydict"]["something"] = "YOLO"


@pytest.mark.parametrize(
    "database",
    [
        pytest.lazy_fixture("sheraf_database"),
        pytest.lazy_fixture("sheraf_zeo_database"),
        #    pytest.lazy_fixture("sheraf_pgsql_relstorage_database"),
    ],
)
def test_different_item_modification_no_conflict(database):
    database.nestable = True

    with sheraf.connection(commit=True) as conn:
        conn.root()["mydict"] = sheraf.types.SmallDict(
            {"something": None, "something_else": None}
        )

    with sheraf.connection(commit=True) as conn1:

        with sheraf.connection(commit=True) as conn2:
            conn2.root()["mydict"]["something"] = "conn2"

        conn1.root()["mydict"]["something_else"] = "conn1"


@pytest.mark.parametrize(
    "database",
    [
        pytest.lazy_fixture("sheraf_database"),
        pytest.lazy_fixture("sheraf_zeo_database"),
        #    pytest.lazy_fixture("sheraf_pgsql_relstorage_database"),
    ],
)
def test_same_item_different_modification_conflict(database):
    database.nestable = True

    with sheraf.connection(commit=True) as conn:
        conn.root()["mydict"] = sheraf.types.SmallDict({"something": None})

    with sheraf.connection() as conn1:

        with sheraf.connection(commit=True) as conn2:
            conn2.root()["mydict"]["something"] = "conn2"

        conn1.root()["mydict"]["something"] = "conn1"

        with pytest.raises(ZODB.POSException.ConflictError):
            conn1.transaction_manager.commit()

    with sheraf.connection() as conn:
        assert "conn2" == conn.root()["mydict"]["something"]
