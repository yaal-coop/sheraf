Model indexation
================

Sheraf provides a way to quickly access your data matching some criterias. This section shows how to take advantage of sheraf indexes.

.. contents::
   :local:

Faster filtering and ordering
-----------------------------

With large collections, searching for models with :func:`~sheraf.queryset.QuerySet.filter` can be very long. Indeed, the default behavior of :func:`~sheraf.queryset.QuerySet.filter` is to scan every available model, and tests its values.

.. code-block:: python

    >>> # The following statements have equal complexity
    >>> MyModel.filter(my_attribute="something") # doctest: +SKIP
    >>> (model for model in MyModel.all() if model.my_attribute == "something") # doctest: +SKIP

Of course all the models are not loaded in memory at once due to the lazy behavior of :class:`~sheraf.queryset.QuerySet`, but the iteration still need to make numerous accesses to the database, and test every model instance, thus severely degrading the performances.

A solution to keep good performances is to use attribute indexation with :func:`~sheraf.attributes.base.BaseAttribute.index`. Indexing an attribute creates a new index table in the database. This table matches the model instances with their attribute values. Any piece of code that works with a non-indexed attribute will have the very same behavior, but faster. So migrations are painless.

.. code-block:: python

    >>> class Cowboy(sheraf.Model):
    ...     table = "simple_cowboy"
    ...     name = sheraf.SimpleAttribute().index()
    ...
    >>> with sheraf.connection(commit=True) as conn:
    ...     george = Cowboy.create(name="George Abitbol")
    ...
    ...     # A dedicated table has been created for the 'name' index
    ...     assert george.mapping in conn.root()["simple_cowboy"]["name"]["George Abitbol"]
    ...
    ...     # Filtering over names is a lot faster!
    ...     assert [george] == Cowboy.filter(name="George Abitbol")

Attribute indexation also hugely improves the :func:`~sheraf.queryset.QuerySet.order` performances.

.. code-block:: python

    >>> import uuid
    >>> with sheraf.connection(): # doctest: +SKIP
    ...     # Even with a lot of cowboy...
    ...     for i in range(10000):
    ...         Cowboy.create(name=str(uuid.uuid4()))
    ...
    ...     # ... ordering on names is very fast
    ...     assert george in Cowboy.order(name=sheraf.DESC)


Values unicity or multiplicity
------------------------------

.. code-block:: python

    >>> class Cowboy(sheraf.Model):
    ...     table = "unique_cowboy"
    ...     name = sheraf.SimpleAttribute()
    ...     email = sheraf.SimpleAttribute().index(unique=True)

By default, indexed attributes of different model instances can have the same value. There is no issue for two cowboys to be called `George Abitbol`. But in our example, the `email` attribute has a `unique` flag. This means that only one person can have a specific email at a time. Trying to create a second person with `george@abitbol.com` will result in a :class:`~sheraf.exceptions.UniqueIndexException` exception.

.. code-block:: python

    >>> with sheraf.connection(commit=True):
    ...     george = Cowboy.create(name="The true George", email="george@abitbol.com")
    ...
    >>> with sheraf.connection():
    ...     Cowboy.create(name="The fake George", email="george@abitbol.com")
    Traceback (most recent call last):
        ...
    sheraf.exceptions.UniqueIndexException

Note that when an attribute is unique, you can use the :func:`~sheraf.models.indexation.IndexedModel.read` method.

.. code-block:: python

    >>> with sheraf.connection():
    ...     assert george == Cowboy.read(email="george@abitbol.com")

Custom values in the index
--------------------------

Sometimes you may want to transform a value before indexation, or
before querying the database.

Recording custom data
`````````````````````

For instance, what if we would like to index cowboy not its name, but on its initials?

:func:`~sheraf.attributes.base.BaseAttribute.index` takes a `values` argument that is a function
taking the attribute value, and returning a collection of values that should be indexed.

.. code-block:: python

    >>> def initials(name):
    ...     return "".join(word[0] for word in name.split(" "))
    ...
    >>> class Cowboy(sheraf.Model):
    ...     table = "valuable_cowboy"
    ...     name = sheraf.StringAttribute().index(
    ...          values=lambda name: {initials(name)},
    ...     )
    ...
    >>> with sheraf.connection(commit=True):
    ...     george = Cowboy.create(name="George Abitbol")


Here we pass the a *lambda* function that returns the initials of a name inside a python set.
Now it is possible to search for someone only knowing its initials.

.. code-block:: python

    >>> with sheraf.connection():
    ...     assert [george] == Cowboy.filter(name="GA")
    ...     assert [] == Cowboy.filter(name="George Abitbol")

Note that the :func:`~sheraf.queryset.QuerySet.filter` **name** parameter does not go through the same
*lambda* transformation. It search for the exact data in the index.

Reading custom data
```````````````````

Now what if you need to search for the initials of a cowboy based on another cowboy's name?
You could just use the :func:`~sheraf.queryset.QuerySet.search` method to do that.

.. code-block:: python

    >>> with sheraf.connection():
    ...     assert [george] == Cowboy.search(name="Gerard Amsterdam")
    ...     assert [george] == Cowboy.search(name="Geoffrey Abitbol")

You may want to be able to edit the values you pass to *name*. For instance, you may want
your users to be able to search for initials in whatever order they have been passed.

:func:`~sheraf.attributes.base.BaseAttribute.index` takes a `search` argument that is a function
taking the data you want to search, and return a collection of keys to search in the index.
:func:`~sheraf.queryset.QuerySet.search` will search for all the keys in the index, and will
return the matching model instances.
By default the `search` argument takes the same argument than the
:func:`~sheraf.attributes.base.BaseAttribute.index` *values* argument.

.. code-block:: python

    >>> from itertools import permutations
    >>> class Cowboy(sheraf.Model):
    ...     table = "invaluable_cowboy"
    ...     name = sheraf.StringAttribute().index(
    ...         values=lambda name: {initials(name)},
    ...         search=lambda name: {
    ...             "".join(p) for p in permutations(initials(name))
    ...         },
    ...     )
    ...
    >>> with sheraf.connection(commit=True):
    ...     george = Cowboy.create(name="George Abitbol")
    ...
    ...     assert [george] == Cowboy.search(name="Amsterdam Gerard")

Now we index the initials of cowboys, but we search for all the combinations of initials
with the words that are passed to the *search* argument.

Multiple indexes
----------------

What if we want to index birth years and birth months? This is quite straightforward, :func:`~sheraf.attributes.base.BaseAttribute.index` calls can be chained to describe different indexes, and the `key` parameter can be used to identify them.

.. code-block:: python

    >>> class Cowboy(sheraf.Model):
    ...     table = "multiple_cowboy"
    ...     birth = sheraf.DateTimeAttribute() \
    ...         .index(key="year", values=lambda birth: {birth.year}) \
    ...         .index(key="month", values=lambda birth: {birth.month})
    ...
    >>> from datetime import datetime
    >>> with sheraf.connection():
    ...     peter = Cowboy.create(birth=datetime(1989, 4, 13))
    ...     assert [peter] == Cowboy.filter(year=1989)
    ...     assert [peter] == Cowboy.filter(month=4)
    ...     assert [peter] == Cowboy.search(year=datetime(1989, 4, 13))
    ...     assert [peter] == Cowboy.search(month=datetime(1989, 4, 13))

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
    >>> class Cowboy(sheraf.Model):
    ...     table = "deeper_cowboy"
    ...     biography = sheraf.SimpleAttribute().index(values=substrings)
    ...
    >>> with sheraf.connection():
    ...     george = Cowboy.create(
    ...         biography="He is 50, he is a cowboy and he is the most classy man on the world."
    ...     )
    ...     assert [george] == Cowboy.filter(biography="boy")

The ``substrings`` function extracts all the possible substring from all the words in a string. Now you can find a cowboy by searching for any piece of word in his biography.

Migration and checks
--------------------

Now you are convinced that indexes are awesome and you want to add some in your models. You can totally just add a ``.index()`` on your attributes, and everything will go fine...

...except that things may not be faster. This is because indexation is disabled for already populated model tables.
If your database is empty, indexation will work out of the box, but if you already have some models you will get a :class:`~sheraf.exceptions.IndexationWarning` when you will create or edit model instances.

.. code-block:: python

    >>> class Cowboy(sheraf.Model):
    ...     table = "future_cowboys"
    ...     name = sheraf.StringAttribute()
    ...
    >>> with sheraf.connection(commit=True):
    ...     george = Cowboy.create(name="George")
    ...     peter = Cowboy.create(name="Peter")
    ...
    >>> # Now you decide to add indexes in your code
    >>> class Cowboy(sheraf.Model):
    ...     table = "future_cowboys"
    ...     name = sheraf.StringAttribute().index()
    ...
    >>> import warnings
    >>> with sheraf.connection(commit=True):
    ...     with warnings.catch_warnings(record=True) as warns:
    ...         steven = Cowboy.create(name="Steven")
    ...         assert warns[0].category is sheraf.exceptions.IndexationWarning

Sheraf provides tools to check the health of your model tables. So now, let us check how things are going for cowboys:

.. code-block:: python

    >>> from sheraf.batches.checks import print_health
    >>> with sheraf.connection(): : # doctest: +SKIP
    ...     print_health(Cowboy, attribute_checks=["index"])
                 _                     __        _               _
    =========== | | ================= / _| ==== | | =========== | | ===============
             ___| |__   ___ _ __ __ _| |_    ___| |__   ___  ___| | _____
            / __| '_ \ / _ \ '__/ _` |  _|  / __| '_ \ / _ \/ __| |/ / __|
            \__ \ | | |  __/ | | (_| | |   | (__| | | |  __/ (__|   <\__ \
            |___/_| |_|\___|_|  \__,_|_|    \___|_| |_|\___|\___|_|\_\___/
    ===============================================================================
    Analyzing your models, this operation can be very long...
    ===============================================================================
    index                                                         OK       KO
    - __main__.Cowboy_____________________________________ TOTAL: 0_______ 3_______
      - name_____________________________________________________ 0_______ 3_______



You can see here that the indexation table *name* is absent. You can call :func:`~sheraf.models.indexation.IndexedModel.index_table_rebuild` to create and populate it.

.. code-block:: python

    >>> with sheraf.connection(commit=True):
    ...     Cowboy.index_table_rebuild(["name"])

Now that your index table is created and filled, you won't be bothered by an :class:`~sheraf.exceptions.IndexationWarning` anymore.

.. code-block:: python

    >>> with sheraf.connection(commit=True):
    ...     with warnings.catch_warnings(record=True) as warns:
    ...         boss = Cowboy.create(name="Boss")
    ...         assert not warns
