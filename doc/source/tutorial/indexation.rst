Model attribute indexation
==========================

.. contents::
   :local:

Faster filtering and ordering
-----------------------------

With large collections, searching for models with :func:`~sheraf.queryset.QuerySet.filter` can be very long. Indeed, the default behavior of :func:`~sheraf.queryset.QuerySet.filter` is to scan every available model, and tests its values.

.. code-block:: python

    >>> # The following statements have an equal complexity
    >>> MyModel.filter(my_attribute="something") # doctest: +SKIP
    >>> (model for model in MyModel.all() if model.my_attribute == "something") # doctest: +SKIP

Of course all the models are not loaded in memory at once due to the lazy behavior of :class:`~sheraf.queryset.QuerySet`, but the iteration still need to make numerous accesses to the database, thus severely degrading the performances.

A solution to keep good performances is to use attribute indexation with :func:`~sheraf.attributes.base.BaseAttribute.index`. Using :func:`~sheraf.attributes.base.BaseAttribute.index` on an attribute will create in the database a new table matching model instances with their attribute values, but will not change any previous behavior:

.. code-block:: python

    >>> class People(sheraf.Model):
    ...     table = "simple_people"
    ...     name = sheraf.SimpleAttribute().index()
    ...
    >>> with sheraf.connection(commit=True) as conn:
    ...     george = People.create(name="George Abitbol")
    ...
    ...     # A dedicated table has been created for the 'name' index
    ...     assert george._persistent in conn.root()["simple_people"]["name"]["George Abitbol"]
    ...
    ...     # Filtering over names is a lot faster!
    ...     assert [george] == People.filter(name="George Abitbol")

Attribute indexation also hugely improves the :func:`~sheraf.queryset.QuerySet.order` performances.

.. code-block:: python

    >>> import uuid
    >>> with sheraf.connection(): # doctest: +SKIP
    ...     # Even with a lot of people...
    ...     for i in range(10000):
    ...         People.create(name=str(uuid.uuid4()))
    ...
    ...     # ... ordering on names is very fast
    ...     assert george in People.order(name=sheraf.DESC)


Unicity and multiplicity
------------------------

.. code-block:: python

    >>> class People(sheraf.Model):
    ...     table = "unique_people"
    ...     name = sheraf.SimpleAttribute()
    ...     email = sheraf.SimpleAttribute().index(unique=True)

By default, indexed attributes of different model instances can have the same value. There is no issue for two people to be called `George Abitbol`. But in our example, the `email` attribute has a `unique` flag. This means that only one person can have a specific email at a time. Trying to create a second person with `george@abitbol.com` will result in a :class:`~sheraf.exceptions.UniqueIndexException` exception.

.. code-block:: python

    >>> with sheraf.connection(commit=True):
    ...     george = People.create(name="The true George", email="george@abitbol.com")
    ...
    >>> with sheraf.connection():
    ...     People.create(name="The fake George", email="george@abitbol.com")
    Traceback (most recent call last):
        ...
    sheraf.exceptions.UniqueIndexException

Note that when an attribute is unique, you can use the :func:`~sheraf.models.indexation.IndexedModel.read` method.

.. code-block:: python

    >>> with sheraf.connection():
    ...     assert george == People.read(email="george@abitbol.com")

Custom values in the index
--------------------------

Sometimes you may want to transform a value before indexation. For instance, what if we would like to index people not on their birth date, but on their birth year?

:func:`~sheraf.attributes.base.BaseAttribute.index` takes a `values` argument that is a function taking the attribute value, and returning a collection of values that should be indexed.

.. code-block:: python

    >>> class People(sheraf.Model):
    ...     table = "valuable_people"
    ...     birth = sheraf.DateTimeAttribute().index(values=lambda birth: {birth.year})
    ...
    >>> from datetime import datetime
    >>> with sheraf.connection(commit=True):
    ...     peter = People.create(birth=datetime(1989, 4, 13))


Here we pass the function ``lambda birth: {birth.year}`` that returns the birth year inside a python set. Now it is possible to search for someone only knowing its birth year with ``.filter(birth=1989)``.

.. code-block:: python

    >>> with sheraf.connection():
    ...     # Search people whose birth year matches a year
    ...     assert [peter] == People.filter(birth=1989)

Note that the :func:`~sheraf.queryset.QuerySet.filter` **birth** parameter does not go through the same ``lambda birth: {birth.year}`` transformation, so passing a datetime to **birth** will not give any result. Of course searching for a date with another date is not very convenient nor meaningful here, but if you would, you could just use the :func:`~sheraf.queryset.QuerySet.filter_raw` method to do that.

.. code-block:: python

    >>> with sheraf.connection():
    ...     assert [peter] == People.filter_raw(birth=datetime(1989, 4, 13))
    ...     assert [peter] == People.filter_raw(birth=datetime(1989, 6, 10))

To summarize :func:`~sheraf.queryset.QuerySet.filter_raw` applies the values transformation to its parameters, and :func:`~sheraf.queryset.QuerySet.filter` does not.

Multiple indexes
----------------

What if we want to index birth years and birth months? This is quite straightforward, :func:`~sheraf.attributes.base.BaseAttribute.index` calls can be chained to describe different indexes, and the `key` parameter can be used to identify them.

.. code-block:: python

    >>> class People(sheraf.Model):
    ...     table = "multiple_people"
    ...     birth = sheraf.DateTimeAttribute() \
    ...         .index(key="year", values=lambda birth: {birth.year}) \
    ...         .index(key="month", values=lambda birth: {birth.month})
    ...
    >>> with sheraf.connection():
    ...     peter = People.create(birth=datetime(1989, 4, 13))
    ...     assert [peter] == People.filter(year=1989)
    ...     assert [peter] == People.filter(month=4)
    ...     assert [peter] == People.filter_raw(year=datetime(1989, 4, 13))
    ...     assert [peter] == People.filter_raw(month=datetime(1989, 4, 13))

Index several values at once
----------------------------

The value transformation function must return a collection of values, and every values in the collection will be indexed. So based on his full name, we can index a person first and last name. The idea is that we want to be able to find a person knowing only his first name, or only his last name. For instance, we want to be able to find *George Abitbol* even if we only know his name is *Abitbol*.

.. code-block:: python

    >>> class People(sheraf.Model):
    ...     table = "numerous_people"
    ...     name = sheraf.SimpleAttribute().index(values=lambda name: set(name.split(" ")))
    ...
    >>> with sheraf.connection():
    ...     george = People.create(name="George Abitbol")
    ...     # here the values function produces {'George', 'Abitbol'} and indexes this object
    ...     # for 'George' and 'Abitbol'
    ...
    ...     assert [george] == People.filter(name="George")
    ...     assert [george] == People.filter(name="Abitbol")

Dig a bit deeper
````````````````

We could easilly use this to create a simple full-text search engine on a model attribute with only a few lines:

.. code-block:: python

    >>> from itertools import combinations
    >>> def substrings(string):
    ...     return {
    ...         word[x:y]
    ...         for word in string.split(" ")
    ...         for x, y in combinations(range(len(word)+1), r=2)
    ...     }
    ...
    >>> class People(sheraf.Model):
    ...     table = "deeper_people"
    ...     biography = sheraf.SimpleAttribute().index(values=substrings)
    ...
    >>> with sheraf.connection():
    ...     george = People.create(
    ...         biography="He is 50, he is a cowboy and he is the most classy man on the world."
    ...     )
    ...     assert [george] == People.filter(biography="boy")

Migration and checks
--------------------

To be done.
