import pytest
import sheraf


@pytest.fixture
def other_database():
    database = None
    try:
        database = sheraf.Database("memory://?database_name=other_database")
        yield database
    finally:
        if database:
            database.close()


@pytest.fixture
def other_nested_database():
    database = None
    try:
        database = sheraf.Database(
            "memory://?database_name=other_nested_database", nestable=True
        )
        yield database
    finally:
        if database:
            database.close()
