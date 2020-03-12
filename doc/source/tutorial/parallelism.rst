===========
Concurrency
===========

Let us see how sheraf cowboys behave in parallelize contexts.

.. doctest::
    :hide:

    >>> from tests import utils
    >>> persistent_dir, oldmapping_dir = utils.create_temp_directory()
    >>> zeo_process, zeo_port = utils.start_zeo_server(persistent_dir)
    >>> try:
    ...     sheraf.Database.get().close()
    ... except:
    ...     pass

.. doctest::

    >>> class Cowboy(sheraf.Model):
    ...     table = "cowboys"
    ...     gunskill = sheraf.IntegerAttribute()
    ...
    >>> db = sheraf.Database("zeo://localhost:{}".format(zeo_port))
    ...
    >>> with sheraf.connection(commit=True):
    ...     george = Cowboy.create()

Threading
=========

The :ref:`ZODB documentation <zodb:using-transactions-label>` about concurrency states that database :class:`~ZODB.Connection.Connection`, :class:`~transaction.interfaces.ITransactionManager` and :class:`~transaction.interfaces.ITransaction` are not thread-safe. However ZODB :class:`~ZODB.DB` objects can be shared between threads.

This means that it is possible to create a :class:`~sheraf.databases.Database` object once, and then share it on several threads. However each thread should use its own connection context:

.. doctest::

    >>> import threading
    >>> def practice_gun(cowboy_id):
    ...     # The database is available in children thread, but they
    ...     # need to open their own connection contexts.
    ...     with sheraf.connection(commit=True):
    ...         cowboy = Cowboy.read(cowboy_id)
    ...         cowboy.gunskill = cowboy.gunskill + 1000
    ...
    >>> practice_session = threading.Thread(target=practice_gun, args=(george.id,))
    >>> practice_session.start()
    >>> practice_session.join()
    ...
    >>> with sheraf.connection():
    ...     Cowboy.read(george.id).gunskill
    1000

Opening a thread within a connection context will produce various unexpected behaviors.

Multiprocessing
===============

When using multiprocessing, the behavior is a bit different. The :class:`~sheraf.database.Database` are not shared between processes.

.. doctest::

    >>> import multiprocessing
    >>> practice_session = multiprocessing.Process(target=practice_gun, args=(george.id,))
    >>> practice_session.start()
    >>> practice_session.join()
    >>> practice_session.exitcode
    1

The connection context in the ``practice_gun`` function has raised a :class:`KeyError` exception because in this new process, no database has been defined. Fortunately there is a simple solution to this. The database needs to be redefined in the new process:

.. doctest::

    >>> def recreate_db_and_practice_gun(cowboy_id):
    ...     # The database is re-created in the child process
    ...     db = sheraf.Database("zeo://localhost:{}".format(zeo_port))
    ...
    ...     with sheraf.connection(commit=True):
    ...         cowboy = Cowboy.read(cowboy_id)
    ...         cowboy.gunskill = cowboy.gunskill + 1000
    ...     db.close()
    ...
    >>> practice_session = multiprocessing.Process(target=recreate_db_and_practice_gun, args=(george.id,))
    >>> practice_session.start()
    >>> practice_session.join()
    ...
    >>> with sheraf.connection():
    ...     Cowboy.read(george.id).gunskill
    2000

.. note::

    Remember that :class:`~ZODB.FileStorage.FileStorage.FileStorage`, :class:`~ZODB.MappingStorage.MappingStorage` and :class:`~ZODB.DemoStorage.DemoStorage` cannot be used by several processes.

.. doctest::
    :hide:

    >>> db.close()
    >>> utils.stop_zeo_server(zeo_process, silent=True)
    >>> utils.delete_temp_directory(persistent_dir, oldmapping_dir)
