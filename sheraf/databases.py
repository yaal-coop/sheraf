"""Databases."""

import contextlib
import os
import threading
import traceback

import transaction
import ZODB.config
import ZODB.DB
import zodburi
from ZODB.DemoStorage import DemoStorage

from sheraf.exceptions import ConnectionAlreadyOpened


class LocalData:
    instance = None

    def __init__(self):
        self.pid = os.getpid()
        self.databases = {}
        self.last_database_context = {}
        self.zodb_databases = {}

        class GlobalThreadContext(threading.local):
            def __init__(self):
                super().__init__()
                self.connections = []
                self.last_connection_context = None

        self.thread_context = GlobalThreadContext()

    @classmethod
    def get(cls):
        # TODO: put a lock on pid
        if not cls.instance or cls.instance.pid != os.getpid():
            cls.instance = LocalData()
        return cls.instance


class Database(object):
    """A ZODB :class:`ZODB.DB` wrapper with a :class:`ZODB.interfaces.IStorage`
    factory.

    The storage factory will either create a
    :class:`ZEO.ClientStorage.ClientStorage`, a
    :class:`ZODB.FileStorage.FileStorage.FileStorage`, a
    :class:`ZODB.DemoStorage.DemoStorage`, a Relstorage
    :class:`~relstorage.adapters.postgresql.adapter.PostgreSQLAdapter` or use a
    user defined storage depending on the argument passed at the initialization
    of the object.

    A Storage object is created and pass it to the :class:`ZODB.DB` constructor

    Several connections can be used at the same time. The connections are
    identified by their name.

    :param database_name: The name of the connection.
    :param storage: If set, this user defined storage will be used.
    :param uri: A zodburi to the database.
    :type uri: An URI that will be parsed by :func:`zodburi.resolve_uri`.
    :param db_args: Arguments to pass to the :class:`ZODB.DB`.

    :param nestable: If `False`, will raise a
        :class:`~sheraf.exceptions.ConnectionAlreadyOpened` if a connection has
        already been opened.
    """

    DEFAULT_DATABASE_NAME = "unnamed"

    def __init__(self, uri=None, storage=None, nestable=False, db_args=None):
        self.nestable = nestable
        self.uri = uri
        self.db = None
        self.storage = None
        self.db_args = db_args or {}

        class DatabaseThreadContext(threading.local):
            def __init__(self):
                super().__init__()
                self.connections = []

        self.thread_context = DatabaseThreadContext()

        self.db_args["databases"] = LocalData.get().zodb_databases

        self.reset(storage, uri)

        stack = traceback.extract_stack()[-2]
        LocalData.get().last_database_context[self.name] = (
            stack.filename,
            stack.lineno,
        )

    def __repr__(self):
        description = "<Database database_name='{}'".format(self.name)

        if self.db_args.get("read_only", False):
            description += " ro"

        if self.nestable:
            description += " nestable"

        description += ">"
        return description

    def reset(self, storage=None, uri=None):
        """Close and reopen a database connection."""
        if self.db:
            self.close()

        if storage is not None:
            self.storage = storage

        elif uri:
            storage_factory, db_args = zodburi.resolve_uri(uri)
            self.storage = storage_factory()
            db_args.update(self.db_args)
            self.db_args = db_args

        else:
            self.storage = DemoStorage()

        self.name = self.db_args.get("database_name", Database.DEFAULT_DATABASE_NAME)
        if self.name in LocalData.get().databases:
            last_context = LocalData.get().last_database_context.get(self.name)
            raise KeyError(
                "A database named '{}' already exists. Last opening was on {} at line {}".format(
                    self.name, last_context[0], last_context[1]
                )
                if last_context
                else "A database named '{}' already exists.".format(self.name)
            )

        self.db = ZODB.DB(self.storage, **self.db_args)
        LocalData.get().databases[self.name] = self

    def connection_open(self):
        """Opens a connection. Returns a connection to this database.

        If `nestable` is set and a connection has already been opened,
        raises a :class:`~sheraf.exceptions.ConnectionAlreadyOpened` exception.
        If `nestable` is False
        and a connection has already been opened, it returns a new connection
        with a new transaction_manager.

        :return: A :class:`~ZODB.Connection.Connection` object.
        """
        data = LocalData.get()

        # No other connection exists
        if not Database.last_connection():
            connection = self.db.open()

        # A connection to this database exists, and the second one is not allowed.
        elif not self.nestable:
            message = (
                "First connection was {} on {} at line {}".format(
                    Database.last_connection(),
                    *data.thread_context.last_connection_context
                )
                if data.thread_context.last_connection_context
                else "First connection was {}".format(Database.last_connection())
            )
            raise ConnectionAlreadyOpened(message)

        # A connection to this database exists, and the second one is allowed, but
        # with a new transaction manager.
        else:
            connection = self.db.open(
                transaction_manager=transaction.TransactionManager()
            )

        self.thread_context.connections.append(connection)
        data.thread_context.connections.append(connection)
        return connection

    def connection_close(self, connection=None):
        """Closes a connection opened on the database.

        :param connection: The connection to close, if `None` the last
            connection opened on the database is closed.
        """
        connection = connection or Database.last_connection(self)
        if connection.opened:
            connection.close()

        if connection in LocalData.get().thread_context.connections:
            LocalData.get().thread_context.connections.remove(connection)

        if connection in self.thread_context.connections:
            self.thread_context.connections.remove(connection)

    def close(self):
        """Closes the database."""
        data = LocalData.get()
        for connection in list(self.thread_context.connections):
            if connection and connection.opened:
                connection.close()
            data.thread_context.connections.remove(connection)
            self.thread_context.connections.remove(connection)

        if self.db:
            self.db.close()

        if self.name in data.databases:
            del data.databases[self.name]

        if self.name in data.zodb_databases:
            del data.zodb_databases[self.name]

        if self.name in data.last_database_context:
            del data.last_database_context[self.name]

        self.db = None
        self.storage = None

    @contextlib.contextmanager
    def connection(self, commit=False, cache_minimize=False, _trackeback_shift=0):
        """A context manager opening a connection on this database.

        :param commit: Whether to commit the transaction when leaving the
            context manager.
        :type commit: boolean
        :param cache_minimize: Whether to call
            :func:`ZODB.Connection.Connection.cache_minimize` when leaving the
            context manager.
        :type cache_minimize: boolean


        >>> database = sheraf.Database()
        >>> with database.connection() as connection:
        ...    sheraf.Database.current_connection() is connection
        True
        """
        _connection = self.connection_open()
        if not self.nestable:
            stack = traceback.extract_stack()[-3 - _trackeback_shift]
            LocalData.get().thread_context.last_connection_context = (
                stack.filename,
                stack.lineno,
            )

        try:
            yield _connection
            if commit:
                _connection.transaction_manager.commit()

        except BaseException:
            if commit and _connection.transaction_manager:
                _connection.transaction_manager.abort()
            raise

        finally:
            # TODO: to be changed with try/except NoTransaction when upgrading transaction>2.0 @cedric
            if not commit and _connection.transaction_manager:
                _connection.transaction_manager.abort()

            if cache_minimize:
                for conn in _connection.connections.values():
                    conn.cacheMinimize()

            self.connection_close(_connection)

    @classmethod
    def last_connection(cls, database=None):
        if database:
            return (
                database.thread_context.connections[-1]
                if database.thread_context.connections
                else None
            )
        return (
            LocalData.get().thread_context.connections[-1]
            if LocalData.get().thread_context.connections
            else None
        )

    @classmethod
    def current_connection(cls, database_name=None):
        if not Database.last_connection():
            return None

        if not database_name:
            return Database.last_connection()

        return Database.last_connection().get_connection(database_name)

    @classmethod
    def current_name(cls):
        if Database.last_connection():
            return Database.last_connection().db().database_name
        return None

    @classmethod
    def all(cls):
        """
        :return: A list containing all the existing :class:`Database` in a
            tuple `(name, Database)`.
        """
        return LocalData.get().databases.items()

    @classmethod
    def get(cls, database_name=None):
        """
        :param database_name: The name of the queried database.
        :return: The database object if it exists. A :class:`KeyError` is raised elsewise.
        """
        database_name = database_name or Database.DEFAULT_DATABASE_NAME
        try:
            return LocalData.get().databases[database_name]
        except KeyError:
            raise KeyError("No database named '{}'.".format(database_name))

    @classmethod
    def get_or_create(cls, **kwargs):
        """
        :return: The database object if it exists. If the database does not exist, it is created with the `kwargs` arguments.
        """
        try:
            return Database.get(database_name=kwargs.get("database_name"))
        except KeyError:
            return Database(**kwargs)


@contextlib.contextmanager
def connection(database_name=None, commit=False, cache_minimize=False):
    database = Database.get(database_name)
    with database.connection(
        commit=commit,
        cache_minimize=cache_minimize,
        _trackeback_shift=2,
    ) as conn:
        yield conn
