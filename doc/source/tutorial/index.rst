==========
 Tutorial
==========

.. toctree::
    :glob:
    :maxdepth: 2

    **

.. doctest::
    :hide:

    >>> try:
    ...     sheraf.Database.get().close()
    ... except:
    ...     pass

TODO (on going work. See documentation branch for an extended tutorial)

Preamble: we defined on purpose a quite close mapping to the ZODB introduction examples as seen here:
`ZODB (External link) <http://www.zodb.org/en/latest/articles/ZODB1.html>`_


Start creating your first sheraf database with the following steps!

1. Create a storage and a first simple model
=================================================

Let us first create a sheraf :class:`~sheraf.databases.Database`
instance. It takes a "storage object" (see
`Storage API <http://www.zodb.org/en/latest/reference/storages.html#included-storages>`_) in parameter, telling how and
where data will be stored. The created instance is a default database that is
available as a global variable.

.. doctest::

   >>> from ZODB.DemoStorage import DemoStorage
   >>> import sheraf
   >>> # DemoStorage is a ZODB storage implementation for storing objects
   >>> # temporarily. Use FileStorage to store objects in a file.
   >>> sheraf.Database(storage=DemoStorage())
   <Database database_name='unnamed'>

Before opening the database, we create a simple model, much as a
regular class. To be interpreted as a database model, it suffices to
make it inherit a sheraf class :class:`~sheraf.Model` or a sub-class of it.


.. note::

   ZODBNOTE: when an instance of a sheraf class is created, it is
   mapped to a persistent version of it, through the attribute
   `_persistent` of this class.  The classes of all the objects
   stored in this attribute are descendent of the `Persistent
   <http://www.zodb.org/en/latest/articles/ZODB1.html#persistent-classes>`_
   class from ZODB, allowing zodb to be aware of changes in any
   instance of this model, and applying them when a transaction is
   committed. (see e.g.  SmallDict, LargeList, etc.)

.. doctest::

    >>> class Cowboy(sheraf.Model):
    ...     table = "cowboys"
    ...     name = sheraf.StringAttribute()


Then, this database can be updated by opening a context manager. It
corresponds to opening a connection to the database. You can make
analogy with a file in which you will read/write data with `with
io.open(...)`). With the commit parameter, you tell the database to
commit the transaction, i.e. to update objects before leaving the context.

.. doctest::

    >>> with sheraf.connection(commit=True):
    ...     c = Cowboy.create()
    ...     c.name = "Calamity Jane"

.. note::
  ZODBNOTE: Creation action adds the object `c` to the database ZODB’s `root`.

Now, we can close the database:

.. doctest::

   >>> sheraf.Database.get().close()
