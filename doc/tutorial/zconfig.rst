Databases
=========

Database connections are handled with :class:`~sheraf.databases.Database` objects. Under the hood the handled objects are regular ZODB :class:`~ZODB.DB` object. Generally you can configure your :class:`~sheraf.databases.Database` with a `zodburi <https://docs.pylonsproject.org/projects/zodburi/en/latest/>`_, but if you do not pass any argument, a temporary in-memory database will be created.

Depending on the cases you might want to use:

- A in-memory database with :class:`~ZODB.DemoStorage.DemoStorage`;
- A file database with :class:`~ZODB.FileStorage.FileStorage.FileStorage`;
- A client-server based database with ZEO :class:`~ZEO.ClientStorage.ClientStorage`;
- A client-server over a PostgreSQL server with :class:`~relstorage.adapters.postgresql.adapter.PostgreSQLAdapter`.

Initializing a database context is done by simply creating a :class:`~sheraf.databases.Database` object.

.. code-block:: python

    >>> db = sheraf.Database("zeo://localhost:8000"): # doctest: +SKIP

The database context is now created, but to handle data you need to open a connection to the database.

Database connections
--------------------

The easiest way to open a connection is to use the :meth:`~sheraf.databases.Database.connection` context manager:

.. code-block:: python

    >>> with db.connection(): # doctest: +SKIP
    ...     m = MyModel.create()
    ...     # do other things

The :func:`~sheraf.databases.connection` shortcut allows you to not depend on your :class:`~sheraf.databases.Database` object, by just passing a database name.

.. code-block:: python

    >>> with sheraf.connection("default"): # doctest: +SKIP
    ...     m = MyModel.create()
    ...     # do other things

There is another shortcut: if you try to open a connection to the default database, you do not need to pass it to the :func:`~sheraf.databases.connection` function.'

.. code-block:: python

    >>> with sheraf.connection(): # doctest: +SKIP
    ...     m = MyModel.create()
    ...     # do other things

In a context with only one database, this generally the method most database connections are done.

You can also use it as a function decorator:

.. code-block:: python

    >>> @sheraf.connection()
    ... def do_thing(): # doctest: +SKIP
    ...     m = MyModel.create()
    ...     # do other things
    ...
    >>> do_thing()

.. warning::  Note that by default, you cannot open two connections to the same database:

.. code-block:: python

    >>> with sheraf.connection(): # doctest: +SKIP
    ...     with sheraf.connection():
    ...         m = MyModel.create()
    Traceback (most recent call last):
        ...
    sheraf.exceptions.ConnectionAlreadyOpened: First connection was <Connection at ...> on ... at line ...

Transactions and commits
------------------------

A :class:`~transaction.interfaces.ITransaction` is opened each time you open a connection to a database. If you want to validate the modifications you made on your model, you can use the ``commit`` argument:

.. code-block:: python

    >>> with sheraf.connection(commit=True): # doctest: +SKIP
    ...     m = MyModel.create()
    ...     # do other things
    ...
    >>> @sheraf.connection(commit=True)
    ... def do_thing(): # doctest: +SKIP
    ...     m = MyModel.create()
    ...     # do other things
    ...
    >>> do_thing()

Another option is to use the :func:`~sheraf.transactions.commit` shortcut:

.. code-block:: python

    >>> with sheraf.connection(): # doctest: +SKIP
    ...     m = MyModel.create()
    ...     # do other things
    ...     sheraf.commit()

If you made risky modifications, for instance something with probabilities to raise
:class:`~ZODB.POSException.ConflictError`, you might want to make several attempts so
you can reread the data, and maybe avoid the conflict at the second try. For this you can
use the :func:`~sheraf.transactions.attempt` function:

.. code-block:: python

    >>> def do_thing(): # doctest: +SKIP
    ...     m = MyModel.create()
    ...     # do other things
    ...
    >>> sheraf.attempt(do_thing)

ZConfig file
------------

Instead of passing arguments to :class:`~sheraf.databases.Database`, you can configure your database connections with a configuration files. It is done through a `zodburi <https://docs.pylonsproject.org/projects/zodburi/en/latest/#zconfig-uri-scheme>`_ ``zconfig://`` URI scheme.

A simple example ZConfig file:

.. code-block:: xml

    <zodb>
        <mappingstorage>
        </mappingstorage>
    </zodb>


If that configuration file is located at ``/etc/myapp/zodb.conf``, use the following uri argument to initialize your object:

.. code-block:: python

    >>> sheraf.Database("zconfig:///etc/myapp/zodb.conf") # doctest: +SKIP

A ZConfig file can specify more than one database. Don't forget to specify database-name in that case to avoid conflict on name. For instance:

.. code-block:: xml

    <zodb temp1>
        database-name database1
        <mappingstorage>
        </mappingstorage>
    </zodb>
    <zodb temp2>
        database-name database2
        <mappingstorage>
        </mappingstorage>
    </zodb>

In that case, use a URI with a fragment identifier:

.. code-block:: python

    >>> db1 = sheraf.Database("zconfig:///etc/myapp/zodb.conf#temp1") # doctest: +SKIP
    <Database database1>
    >>> db2 = sheraf.Database("zconfig:///etc/myapp/zodb.conf#temp2") # doctest: +SKIP
    <Database database2>

If not specified in the conf file or in the arguments passed at the initialization of the object, default zodburi values will be used:

* database name: unnamed
* cache size: 5000
* cache size bytes: 0

Note that arguments passed at the initialization of the object override the conf file.

Modifying the data into the database is done with a context manager:

.. code-block:: python

    >>> with sheraf.connection(database_name="database1"): # doctest: +SKIP
    ...     # currently connected to db1
    ...     pass

If the database name is not defined, the ``database_name`` parameter is optional.
