Database connection
===================

As ZODB databases and storages, sheraf :class:`~sheraf.databases.Database` can be configured using a configuration file.
It is done through a `zodburi <https://docs.pylonsproject.org/projects/zodburi/en/latest/#zconfig-uri-scheme>`_ ``zconfig://`` URI scheme.

A simple example ZConfig file:

.. code-block:: xml

    <zodb>
        <mappingstorage>
        </mappingstorage>
    </zodb>


If that configuration file is located at /etc/myapp/zodb.conf, use the following uri argument to initialize your object:

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

If the database name is not defined, the 'database_name' parameter is optional.
