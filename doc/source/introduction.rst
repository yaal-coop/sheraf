Introduction
============

Why use sheraf?
---------------

Sheraf allows you to create models, and indexing them. Using sheraf
should be somewhat similar to other ORM like `SQLAlchemy`_ or `Django`_ ORM.
However the database backend of sheraf is `ZODB`_, so it is fully pythonic.

Here is a quick example of sheraf usage:

    >>> # Declare a model with attributes
    ... class Cowboy(sheraf.Model):
    ...     name = sheraf.StringAttribute().index(unique=True)
    ...     age = sheraf.IntegerAttribute()
    ...
    >>> # Create a model instance and store it in the database
    ... with sheraf.connection(commit=True):
    ...     Cowboy.create(name="George Abitbol", age=51)
    <Cowboy id=...>
    >>> # Find the model based on its indexed parameters
    ... with sheraf.connection():
    ...     george = Cowboy.read(name="George Abitbol")
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
  parts of your object you want to save. Sheraf propose a unique - but flexible - way
  to define models, and take care of the saving mechanism for you.
- **Indexation**: ZODB does not provide an *indexation* layer. Instead it provides you
  datastructures like `BTrees`_ and let you use them as you like to index your data.
  sheraf use those datastructures to offer an unified - but flexible - way to index your
  models. Indexing a model on one of its attributes is generally one line of code away.
- **Migrations**: This is a work still in progress, but sheraf aims to offer a complete
  set of tools to painlessly migrate your data.

Who are we?
-----------

`Yaal`_ is a company based in Bordeaux, France. We are specialized in python development,
and we are FOSS lovers. We have been using sheraf in production for years, and in 2020 we
have cleaned the code and opened the sourcecode.

.. _SQLAlchemy: https://docs.sqlalchemy.org/
.. _Django: https://docs.djangoproject.com
.. _ZODB: https://zodb-docs.readthedocs.io
.. _BTrees: https://btrees.readthedocs.io
.. _Yaal: https://yaal.fr
