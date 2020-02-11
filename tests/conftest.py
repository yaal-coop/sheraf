# TODO: Use pytest-sheraf module instead of those fixtures

import pytest

import sheraf.databases
from .utils import (
    close_database,
    create_blob_directory,
    create_database,
    create_temp_directory,
    delete_temp_directory,
    start_postgresql_server,
    start_zeo_server,
    stop_postgresql_server,
    stop_zeo_server,
)


def load_database_kwargs(request, default=None):
    if not request.cls:
        return default or {}

    db_kwargs = default or {}

    if hasattr(request.cls, "sheraf_database_kwargs"):
        db_kwargs = request.cls.sheraf_database_kwargs

    if hasattr(request.cls, "sheraf_database_extra_kwargs"):
        db_kwargs.update(request.cls.sheraf_database_extra_kwargs)

    return db_kwargs


@pytest.fixture
def sheraf_temp_dir():
    """Creates a temporary directory to store sheraf data.

    :return: The directory path
    """
    temp_directory, old_files_root_dir = create_temp_directory()
    try:
        yield temp_directory
    finally:
        delete_temp_directory(temp_directory, old_files_root_dir)


@pytest.fixture
def sheraf_database(request):
    """This fixture creates a database.

    If a test needs to pass arguments to the database creation, it must be a
    method of a class defining ``sheraf_database_kwargs`` or/and
    ``sheraf_database_extra_kwargs``.
    If ``sheraf_database_kwargs`` is defined, it will overwrite the default
    (empty) arguments dictionnary. If ``sheraf_database_extra_kwargs`` defined,
    the arguments dictionnary will be updates by its values.

    By default, a in-memory database is created with
    :class:`~ZODB.DemoStorage.DemoStorage`.

    >>> def test_something(sheraf_database):
    ...     with sheraf.connection(commit=True):
    ...         MyModel.create()
    ...
    >>> class TestSomething:
    ...     sheraf_database_extra_kwargs = {"database_name": "foobar_db"}
    ...
    ...     def test_something(self, sheraf_database):
    ...         assert "foobar_db" == sheraf_database.name
    """

    db_kwargs = load_database_kwargs(request)
    temp_directory, old_files_root_dir = create_temp_directory()
    database = None
    try:
        database = create_database(db_kwargs)
        yield database

    finally:
        close_database(database)
        delete_temp_directory(temp_directory, old_files_root_dir)


@pytest.fixture
def sheraf_connection(sheraf_database):
    """This fixture opens a connection on a database.

    >>> def test_something(sheraf_connection):
    ...     MyModel.create()
    """
    connection = sheraf_database.connection_open()
    try:
        yield connection
    finally:
        connection.transaction_manager.abort()
        sheraf_database.connection_close(connection)


@pytest.fixture
def sheraf_filestorage_database(request):
    """This fixture creates a database using a
    :class:`~ZODB.FileStorage.FileStorage`."""

    temp_directory, old_files_root_dir = create_temp_directory()
    db_kwargs = load_database_kwargs(
        request, {"uri": "file:///{}/Data.fs".format(temp_directory)}
    )

    database = None
    try:
        database = create_database(db_kwargs)
        yield database

    finally:
        close_database(database)
        delete_temp_directory(temp_directory, old_files_root_dir)


@pytest.fixture(scope="session")
def sheraf_zeo_server():
    """This fixture launches a ZEO server."""
    temp_directory, old_files_root_dir = create_temp_directory()
    blob_dir = create_blob_directory(temp_directory)
    zeo_process, zeo_port = start_zeo_server(temp_directory, blob_dir)
    yield zeo_port, blob_dir
    stop_zeo_server(zeo_process)
    delete_temp_directory(temp_directory, old_files_root_dir)


@pytest.fixture
def sheraf_zeo_database(request, sheraf_zeo_server):
    """This fixture launches a ZEO server, and then creates a database using a
    :class:`~ZEO.ClientStorage`.

    .. note :: Only one ZEO server is launched by test session.
    """

    db_kwargs = load_database_kwargs(
        request,
        {
            "uri": "zeo://localhost:{}?blob_dir={}&shared_blob_dir=true".format(
                *sheraf_zeo_server
            )
        },
    )

    database = None
    try:
        database = create_database(db_kwargs)
        yield database

    finally:
        if database:
            with sheraf.databases.connection(commit=True) as conn:
                for key in list(conn.root().keys()):
                    del conn.root()[key]
        close_database(database)


@pytest.fixture(scope="session")
def sheraf_pgsql_server():
    """This fixture launches a PostgreSQL server, if available."""

    temp_directory, old_files_root_dir = create_temp_directory()
    pg_process, pg_user, pg_port, pg_error = start_postgresql_server(temp_directory)
    if pg_error:
        pytest.skip(pg_error)
    yield pg_user, pg_port
    stop_postgresql_server(pg_process)
    delete_temp_directory(temp_directory, old_files_root_dir)


@pytest.fixture
def sheraf_pgsql_relstorage_database(request, sheraf_pgsql_server):
    """This fixture launches a PostgreSQL server, and then creates a database
    using a :class:`~relstorage.storage.RelStorage`.

    .. note :: Only one PostgreSQL server is launched by test session.
    """

    db_kwargs = load_database_kwargs(
        request, {"uri": "postgres://{}@localhost:{}/zodb".format(*sheraf_pgsql_server)}
    )

    database = None
    try:
        database = create_database(db_kwargs)
        yield database

    finally:
        if database:
            with sheraf.databases.connection(commit=True) as conn:
                for key in list(conn.root().keys()):
                    del conn.root()[key]
        close_database(database)
