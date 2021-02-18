Introduction
============

Why use sheraf?
---------------

Sheraf allows you to create models, and indexing them in a database. Using sheraf
should be somewhat similar to other ORM like `MongoEngine`_, `SQLAlchemy`_ or `Django`_ ORM.
However the database backend of sheraf is a fully pythonic `ZODB`_.

General concepts
----------------

sheraf is about storing and reading data in a database. You will mainly encounter the
following objects:

- :class:`~sheraf.models.base.BaseModel` represents a coherent set of data you want
  to store in a database;
- :class:`~sheraf.attributes.Attribute` are model parameters that will
  serialize and deserialize your data. They come in several flavors such as
  :class:`int`, :class:`string`, etc.
- :class:`~sheraf.attributes.index.Index` are model parameters that will control how
  you register and how you search for a model in the database;
- :class:`~sheraf.queryset.QuerySet` holds the result of a model search;
- :class:`~sheraf.databases.Database` holds the connection context to your database.

Here is a quick example of sheraf usage:

    >>> # Declare a model with attributes
    ... class Cowboy(sheraf.Model):
    ...     first_name = sheraf.StringAttribute()
    ...     last_name = sheraf.StringAttribute()
    ...     age = sheraf.IntegerAttribute()
    ...
    ...     name = sheraf.Index(first_name, last_name, unique=True)
    ...
    >>> # Initialize a database context
    ... sheraf.Database("zeo://localhost:8000"): # doctest: +SKIP
    ...
    >>> # Open a connection to the database
    ... with sheraf.connection(commit=True):
    ...     # Create a model instance and store it in the database
    ...     Cowboy.create(first_name="George", last_name="Abitbol", age=51)
    <Cowboy id=...>
    >>> with sheraf.connection():
    ...     # Find the model based on its indexed parameters
    ...     cowboys = Cowboy.search(name="Abitbol")
    ...
    ...     # Unpack the QuerySet
    ...     george = cowboys.get()
    ...     george.age
    51


Why use sheraf instead of plain ZODB?
-------------------------------------

Sheraf aims to provid tools to make the development with ZODB more
quick and easy. The indexation mechanism and the model definition
is taking care of by sheraf, allowing you to avoid boilerplate and focus
on the valuable parts of your application.

- **Models**: ZODB does not provide a *model* layer. Its usage is mainly about storing
  :class:`~persistent.Persistent` objects, and it is up to you to choose which
  parts of your object you want to save. Sheraf propose a unified - but flexible - way
  to define models, and take care of the saving mechanism for you.
- **Indexation**: ZODB does not provide an *indexation* layer. Instead it provides you
  datastructures like `BTrees`_ and let you use them as you like to index your data.
  sheraf use those datastructures to offer an unified - but flexible - way to index your
  models. Indexing a model on one of its attributes is generally one line of code away.
- **Migrations**: This is a work still in progress, but sheraf aims to offer a complete
  set of tools to painlessly migrate your data so your models can smoothly evolve with
  the changes happening in your software.

Sheraf only depends on ZODB and a few side projects (BTrees, persistent etc.), so you
do not need any other project from the Zope/Plone galaxy.

Who are we?
-----------

`Yaal`_ is a cooperative company based in Bordeaux, France. We are specialized in python development,
and we are FOSS lovers. We have been using sheraf in production for years, and in 2020 we
have cleaned the code and opened the sourcecode.

.. _BTrees: https://btrees.readthedocs.io
.. _Django: https://docs.djangoproject.com
.. _MongoEngine: https://docs.mongoengine.org/
.. _SQLAlchemy: https://docs.sqlalchemy.org/
.. _Yaal: https://yaal.coop
.. _ZODB: https://zodb-docs.readthedocs.io
