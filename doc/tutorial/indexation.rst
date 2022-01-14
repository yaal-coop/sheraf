Indexes
=======

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

A solution to keep good performances is to use attribute indexation with :class:`~sheraf.attributes.index.Index`. Creating an :class:`~sheraf.attributes.index.Index` object in a :class:`~sheraf.models.indexation.IndexedModel` creates a new index table in the database. This table matches the model instances with their attribute values.

.. code-block:: python

    >>> class Cowboy(sheraf.Model):
    ...     table = "simple_cowboy"
    ...     name = sheraf.SimpleAttribute()
    ...     nameindex = sheraf.Index("name")
    ...
    >>> with sheraf.connection(commit=True) as conn:
    ...     george = Cowboy.create(name="George Abitbol")
    ...
    ...     # A dedicated table has been created for the 'nameindex' index
    ...     assert george.mapping in conn.root()["simple_cowboy"]["nameindex"]["George Abitbol"].values()
    ...
    ...     # Filtering over names is a lot faster!
    ...     assert [george] == Cowboy.filter(nameindex="George Abitbol")

A shortcut for this is to call the :func:`~sheraf.attributes.Attribute.index` method on attributes. It takes the very same arguments as the :class:`~sheraf.attributes.index.Index` object, but the index will have the same name as the attribute.
Any piece of code that worked with a non-indexed attribute will have the very same behavior when the attribute is indexed, but faster. So migrations are painless.

.. code-block:: python

    >>> class Cowboy(sheraf.Model):
    ...     table = "simple_cowboy_shortcut"
    ...     name = sheraf.SimpleAttribute().index()
    ...
    >>> with sheraf.connection(commit=True) as conn:
    ...     george = Cowboy.create(name="George Abitbol")
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

Multiple indexes
----------------

What if we want to index birth years and birth months? This is quite straightforward,
:func:`~sheraf.attributes.Attribute.index` calls can be chained to describe
different indexes, and the `key` parameter can be used to identify them.

.. code-block:: python

    >>> class Cowboy(sheraf.Model):
    ...     table = "multiple_cowboy"
    ...     birth = sheraf.DateTimeAttribute() \
    ...         .index(key="year", index_keys_func=lambda birth: birth.year) \
    ...         .index(key="month", index_keys_func=lambda birth: birth.month)
    ...
    >>> from datetime import datetime
    >>> with sheraf.connection():
    ...     peter = Cowboy.create(birth=datetime(1989, 4, 13))
    ...     assert [peter] == Cowboy.filter(year=1989)
    ...     assert [peter] == Cowboy.filter(month=4)
    ...     assert [peter] == Cowboy.search(year=datetime(1989, 4, 13))
    ...     assert [peter] == Cowboy.search(month=datetime(1989, 4, 13))

Custom values in the index
--------------------------

Sometimes you may want to transform a value before indexation, or
before querying the database.

Choose how to record data in the index
``````````````````````````````````````

For instance, what if we would like to index cowboy not its name, but on its initials?

:func:`~sheraf.attributes.Attribute.index` takes a `index_keys_func` argument that is a function
taking the attribute value, and returning a collection of keys on which the model instance should
be indexed.

.. code-block:: python

    >>> def initials(name):
    ...     return "".join(word[0] for word in name.split(" "))
    ...
    >>> class Cowboy(sheraf.Model):
    ...     table = "valuable_cowboy"
    ...     name = sheraf.StringAttribute().index(index_keys_func=initials)
    ...
    >>> with sheraf.connection(commit=True):
    ...     george = Cowboy.create(name="George Abitbol")


Here we pass the a function that returns the initials of a.
Now it is possible to search for someone only knowing its initials.

.. code-block:: python

    >>> with sheraf.connection():
    ...     assert [george] == Cowboy.filter(name="GA")
    ...     assert [] == Cowboy.filter(name="George Abitbol")

Note that the :func:`~sheraf.queryset.QuerySet.filter` **name** parameter will not be
transformed into initials. It search for the exact data in the index.

.. note :: `index_keys_func` functions can return either a single element or a collection of
           elements. Depending on the `noneok` and `nullok`
           :class:`~sheraf.attributes.index.Index` parameters, `None` and falsy index keys might be
           ignored.

Choose how to search data in the index
``````````````````````````````````````

Now what if you need to search for the initials of a cowboy based on another cowboy's name?
You could just use the :func:`~sheraf.queryset.QuerySet.search` method to do that.

.. code-block:: python

    >>> with sheraf.connection():
    ...     assert [george] == Cowboy.search(name="Gerard Amsterdam")
    ...     assert [george] == Cowboy.search(name="Geoffrey Abitbol")

You may want to be able to edit the values you pass to *name*. For instance, you may want
your users to be able to search for initials in whatever order they have been passed.

:func:`~sheraf.attributes.Attribute.index` takes a `search_keys_func` argument that is a function
taking the data you want to search, and return a collection of keys to search in the index.
:func:`~sheraf.queryset.QuerySet.search` will search for all the keys in the index, and will
return the matching model instances.
By default the `search_keys_func` argument takes the same argument than the
:func:`~sheraf.attributes.Attribute.index` *index_keys_func* argument.

.. code-block:: python

    >>> from itertools import permutations
    >>> class Cowboy(sheraf.Model):
    ...     table = "invaluable_cowboy"
    ...     name = sheraf.StringAttribute().index(
    ...         index_keys_func=initials,
    ...         search_keys_func=lambda name: {
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

.. note :: `search_keys_func` functions can return either a single element or a collection of
           elements. If the collection is ordered as in a :class:`list`, then the index
           will be searched in the order of the list.
           If the list contains a same element several times, it will only be returned
           once.


Make custom searchs and recording the default behavior
``````````````````````````````````````````````````````

This `name` attribute and its indexation seems very convenient, so you would like to use
it in other models. Luckily sheraf offers you a way to do this, and cut the boilerplate.
If a :class:`~sheraf.attributes.Attribute` defines some methods called `index_keys`
or `search_keys`, they will be used by default if the :func:`~sheraf.attributes.Attribute.index`
`index_keys_func` and `search_keys_func` are not provided:

.. code-block:: python

    >>> class NameAttribute(sheraf.StringAttribute):
    ...     def index_keys(self, name):
    ...         return initials(name)
    ...
    ...     def search_keys(self, name):
    ...         return {"".join(p) for p in permutations(initials(name))}
    ...
    >>> class Cowboy(sheraf.Model):
    ...     table = "clean_cowboy"
    ...     name = NameAttribute().index()
    ...
    >>> with sheraf.connection(commit=True):
    ...     george = Cowboy.create(name="George Abitbol")
    ...
    ...     assert [george] == Cowboy.search(name="Amsterdam Gerard")

`NameAttribute` can now be used in other models (and it does not need
to be indexed, it just can be).

Some attributes like :class:`~sheraf.attributes.models.ModelAttribute` or collections like
:class:`~sheraf.attributes.collections.ListAttribute` take benefit of this. They allow complex types
like models or collections to be indexed. Generally models are indexed on their identifier, and
every component of a collection is indexed.

.. code-block:: python

    >>> class Horse(sheraf.Model):
    ...     table = "horse"
    ...     name = sheraf.StringAttribute()
    ...
    >>> class Cowboy(sheraf.Model):
    ...     table = "horsed_cowboy"
    ...     horses = sheraf.LargeListAttribute(
    ...         sheraf.ModelAttribute(Horse)
    ...     ).index()
    ...
    >>> with sheraf.connection(commit=True):
    ...     jolly = Horse.create(name="Jolly Jumper")
    ...     george = Cowboy.create(horses=[jolly])
    ...
    ...     assert [george] == Cowboy.search(horses=jolly)


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
    ...     biography = sheraf.SimpleAttribute().index(index_keys_func=substrings)
    ...
    >>> with sheraf.connection():
    ...     george = Cowboy.create(
    ...         biography="He is 50, he is a cowboy and he is the most classy man on the world."
    ...     )
    ...     assert [george] == Cowboy.filter(biography="boy")

The ``substrings`` function extracts all the possible substring from all the words in a string.
Now you can find a cowboy by searching for any piece of word in his biography.

To see how indexes can be used to build a full-text search engine, you can check the :ref:`fts` section.

Indexes over multiple attributes
--------------------------------

It is possible for an index to watch several attributes. To do this you cannot use the
:func:`~sheraf.attributes.Attribute.index` shortcut, so you need to define the
index with a :class:`~sheraf.attributes.index.Index` object.


Here both ``first_name`` and ``last_name`` are indexed in the same place:

.. code-block:: python

    >>> class Cowboy(sheraf.Model):
    ...     table = "common_cowboys"
    ...     first_name = sheraf.StringAttribute()
    ...     last_name = sheraf.StringAttribute()
    ...
    ...     name = sheraf.Index(first_name, last_name)
    ...
    >>> with sheraf.connection():
    ...     george = Cowboy.create(first_name="George", last_name="Abitbol")
    ...     assert george in Cowboy.search(name="George")
    ...     assert george in Cowboy.search(name="Abitbol")

When an index has several attributes, it can have a different indexation methods for each attribute,
and a default one:

.. code-block:: python

    >>> class Cowboy(sheraf.Model):
    ...     table = "advanced_common_cowboys"
    ...     first_name = sheraf.StringAttribute()
    ...     last_name = sheraf.StringAttribute()
    ...     surname = sheraf.StringAttribute()
    ...
    ...     name = sheraf.Index(first_name, last_name, surname)
    ...
    ...     @name.index_keys_func
    ...     def default_name_indexation(self, value):
    ...         return value.lower()
    ...
    ...     @name.index_keys_func(first_name, last_name)
    ...     def full_name_indexation(self, first_name, last_name):
    ...         return f"{first_name} {last_name}".lower()
    ...
    >>> with sheraf.connection():
    ...     george = Cowboy.create(first_name="George", last_name="Abitbol", surname="Georgy")
    ...     assert george in Cowboy.search(name="George Abitbol")
    ...     assert george in Cowboy.search(name="Georgy")
    ...     assert george not in Cowboy.search(name="Abitbol")

Here we used the :meth:`~sheraf.attributes.index.Index.index_keys_func` decorator to define a ``default_name_indexation`` method.
As we did not pass any argument to the decorator, this method is the default indexation method for the index ``name``.
We also defined a ``full_name``. By passing the ``first_name`` and ``last_name`` attributes to the
:meth:`~sheraf.attributes.index.Index.index_keys_func` decorator, we assigned this method to both the attributes, and thus
those very attributes can be indexed at the same time using this method.

Using indexation methods common to several attributes is very useful if you need conditionnal indexation.

.. code-block:: python

    >>> class Cowboy(sheraf.Model):
    ...     table = "little_big_cowboys"
    ...     name = sheraf.StringAttribute()
    ...     sherif = sheraf.BooleanAttribute()
    ...
    ...     sherif_names = sheraf.Index(name, sherif)
    ...
    ...     @sherif_names.index_keys_func(name, sherif)
    ...     def sherif_names_indexation(self, name, sherif):
    ...         return {name} if sherif else {}
    ...
    >>> with sheraf.connection():
    ...     george = Cowboy.create(name="George", sherif=True)
    ...     peter = Cowboy.create(name="Peter", sherif=False)
    ...     assert george in Cowboy.search(sherif_names="George")
    ...     assert peter not in Cowboy.search(sherif_names="George")

The ``sherif_names`` index is updated each time a cowboy ``name`` or ``sherif`` attribute is edited,
and it only contains the names of the sherifes.

Index inheritance
-----------------

Index are inherited the most transparently as you can expect. You can overwrite a parent index, or even create an
index on a parent attribute:

.. code-block:: python

    >>> class Cowboy(sheraf.Model):
    ...     table = "legacy_cowboys"
    ...     first_name = sheraf.StringAttribute()
    ...     last_name = sheraf.StringAttribute()
    ...
    ...     last_name_index = sheraf.Index(last_name, index_keys_func=lambda x: x.lower())
    ...
    >>> class UpperCowboy(Cowboy):
    ...     table = "upper_cowboys"
    ...     last_name_index = sheraf.Index("last_name", index_keys_func=lambda x: x.upper())
    ...     first_name_index = sheraf.Index("first_name", index_keys_func=lambda x: x.upper())
    ...
    >>> with sheraf.connection():
    ...     george = UpperCowboy.create(first_name="george", last_name="abitbol")
    ...     assert george in UpperCowboy.filter(first_name_index="GEORGE")
    ...     assert george in UpperCowboy.filter(last_name_index="ABITBOL")

In the ``Cowboy`` model the ``last_name_index`` stores the names in lowercase, but in the
inherited ``UpperCowboy`` model the index has been overwritten so names are stored in the
index in uppercase. ``UpperCowboy`` also defines a ``first_name_index`` on the ``first_name``
attribute, that is defined in its parent model class.

Health checks and fixes
-----------------------

Now you are convinced that indexes are awesome and you want to add some in your models. You can totally just add a ``.index()`` on your attributes, and everything will go fine...

...except that things may not be faster. This is because indexation is disabled for already populated model tables.
If your database is empty, indexation will work out of the box, but if you already have some instances you will get a :class:`~sheraf.exceptions.IndexationWarning` when you will create or edit model instances.

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

    >>> from sheraf.health import print_health
    >>> with sheraf.connection(): # doctest: +SKIP
    ...     print_health(Cowboy, attribute_checks=["index"])
                 _                     __        _               _
    =========== | | ================= / _| ==== | | =========== | | ===============
             ___| |__   ___ _ __ __ _| |_    ___| |__   ___  ___| | _____
            / __| '_ \ / _ \ '__/ _` |  _|  / __| '_ \ / _ \/ __| |/ / __|
            \__ \ | | |  __/ | | (_| | |   | (__| | | |  __/ (__|   <\__ \
            |___/_| |_|\___|_|  \__,_|_|    \___|_| |_|\___|\___|_|\_\___/
    ===============================================================================
    index                                                         OK       KO
    - __main__.Cowboy_____________________________________ TOTAL: 0_______ 3_______
      - name_____________________________________________________ 0_______ 3_______



You can see here that the indexation table *name* is absent. You can call :func:`~sheraf.models.indexation.IndexedModel.index_table_rebuild` to create and populate it.

.. code-block:: python

    >>> with sheraf.connection(commit=True):
    ...     Cowboy.index_table_rebuild("name")

Now that your index table is created and filled, you won't be bothered by an :class:`~sheraf.exceptions.IndexationWarning` anymore.

.. code-block:: python

    >>> with sheraf.connection(commit=True):
    ...     with warnings.catch_warnings(record=True) as warns:
    ...         boss = Cowboy.create(name="Boss")
    ...         assert not warns
