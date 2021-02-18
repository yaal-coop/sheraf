A tour of model attributes
==========================

Sheraf can store a lot of different objet types. Each type has its own :class:`~sheraf.model.attributes.Attribute` to take care of it.
In this section we will briefly see the most commonly used attributes. For each class the reference will provide more complete information.

.. contents::
   :local:

Introduction
------------

The most simple attribute type is the :class:`~sheraf.attributes.simples.SimpleAttribute`. It can hold anything that an :class:`~BTrees.OOBTree` can store.

.. code-block:: python

    >>> class Cowboy(sheraf.Model):
    ...     table = "cowboy"
    ...     name = sheraf.SimpleAttribute()
    ...
    >>> with sheraf.connection(commit=True):
    ...     george = Cowboy.create(name="George Abitbol")
    ...     george.name
    'George Abitbol'

Default values
~~~~~~~~~~~~~~

Attributes have a **defaut** parameter that can be used to set a default value. For instance let us set the default age for cowboys at 30.

.. code-block:: python

    >>> class Cowboy(sheraf.Model):
    ...     table = "cowboy"
    ...     name = sheraf.SimpleAttribute()
    ...     age = sheraf.SimpleAttribute(default=30)
    ...
    >>> with sheraf.connection(commit=True):
    ...     peter = Cowboy.create(name="Peter", age=35)
    ...     steven = Cowboy.create(name="Steven")
    ...     peter.age
    ...     steven.age
    35
    30

Here **Steven** has not been set an age, so he is **30**.

If the default value is callable, then it will be called. The callable can have zero or one positionnal parameter (that will be the model instance).

.. code-block:: python

    >>> class Cowboy(sheraf.Model):
    ...     table = "cowboy"
    ...     name = sheraf.SimpleAttribute(default=lambda: "John Doe")
    ...
    >>> with sheraf.connection(commit=True):
    ...     john = Cowboy.create()
    ...     john.name
    'John Doe'

Lazyness
~~~~~~~~

Default attributes values are lazy. This means they are not stored in the database until the first read or write access on the attribute. It allows to save some space in the database, and some calculations at the model instance creation. However, this behavior can be disable with the **lazy** parameter:

.. code-block:: python

    >>> class Cowboy(sheraf.Model):
    ...     table = "cowboy"
    ...     name = sheraf.SimpleAttribute(default="John Doe")
    ...     age = sheraf.SimpleAttribute(default=30, lazy=False)
    ...
    >>> with sheraf.connection(commit=True):
    ...     john = Cowboy.create()
    ...     "age" in john.mapping
    ...     "name" in john.mapping
    ...     john.name
    ...     "name" in john.mapping
    True
    False
    'John Doe'
    True

Here we can see that the **age** was stored as soon as the instance was created, but we had to wait to an access to the **name** attribute before it was stored.

Basic attributes
----------------

The simple types such as :class:`int`, :class:`float`, :class:`str`, :class:`str` have their matching :class:`~sheraf.attributes.simples.IntegerAttribute` :class:`~sheraf.attributes.simples.FloatAttribute`, :class:`~sheraf.attributes.simples.StringAttribute` and :class:`~sheraf.attributes.simples.BooleanAttribute`.

All those typed attributes cast their inputs in the type they refers to:

.. code-block:: python

    >>> class Cowboy(sheraf.Model):
    ...     table = "cowboy"
    ...     name = sheraf.StringAttribute()
    ...     age = sheraf.IntegerAttribute()
    ...     height = sheraf.FloatAttribute()
    ...     sherif = sheraf.BooleanAttribute()
    ...
    >>> with sheraf.connection(commit=True):
    ...     george = Cowboy.create(name="George", age=50, height=1.80, sherif=True)
    ...
    ...     george.age = 51.5
    ...     george.age
    51

Here a float ``51.5`` has been passed to an :class:`~sheraf.attributes.simples.IntegerAttribute` and thus has been casted to :class:`int`.


Collections
-----------

Sheraf can also store collection of items. :class:`dict`, :class:`list` and :class:`set` have their matching :class:`~sheraf.attributes.collections.DictAttribute`, :class:`~sheraf.attributes.collections.ListAttribute` and :class:`~sheraf.attributes.collections.SetAttribute`.

Basic usage
~~~~~~~~~~~

.. code-block:: python

    >>> class Cowboy(sheraf.Model):
    ...     table = "cowboy"
    ...     name = sheraf.StringAttribute()
    ...     surnames = sheraf.ListAttribute(persistent_type=sheraf.types.SmallList)
    ...     horse_breeds = sheraf.DictAttribute(persistent_type=sheraf.types.LargeDict)
    ...     favorite_numbers = sheraf.SetAttribute()
    ...
    >>> with sheraf.connection(commit=True):
    ...     george = Cowboy.create(
    ...         name="George Abitbol",
    ...         surnames=["georgy", "the classiest man in the world"],
    ...         horse_breeds={
    ...             "jolly jumper": "mustang",
    ...             "polly pumper": "shetland",
    ...         },
    ...         favorite_numbers={13, 11, 17},
    ...     )
    ...     george.surnames[0]
    ...     george.horse_breeds["jolly jumper"]
    ...     13 in george.favorite_numbers
    'georgy'
    'mustang'
    True

The collection attributes behave the same way than the python types their refer to. You can iterate over a :class:`~sheraf.attributes.collections.ListAttribute` the same way that you can iterate a :class:`list`, you can access data from a :class:`~sheraf.attributes.collections.DictAttribute` the same way you do with a :class:`dict`.

The collection type take a ``persistent_type`` parameter that is the persistent type that will be used to store the data. Sheraf provide some shortcuts to avoid passing this parameter each time you need a collection attribute. You can check :class:`~sheraf.attributes.collections.SmallDictAttribute`, :class:`~sheraf.attributes.collections.LargeDictAttribute`, :class:`~sheraf.attributes.collections.SmallListAttribute` and :class:`~sheraf.attributes.collections.LargeListAttribute`.

Nesting attributes
~~~~~~~~~~~~~~~~~~

Collection attributes can hold other attributes. For instance, you can nest a :class:`~sheraf.attributes.simples.IntegerAttribute` inside a :class:`~sheraf.attributes.collections.LargeListAttribute`:

.. code-block:: python

    >>> class Cowboy(sheraf.Model):
    ...     table = "cowboy"
    ...     name = sheraf.StringAttribute()
    ...     favorite_numbers = sheraf.LargeListAttribute(sheraf.IntegerAttribute())
    ...
    >>> with sheraf.connection(commit=True):
    ...     george = Cowboy.create(
    ...         name="george",
    ...         favorite_numbers=[15, 3.5],
    ...     )
    ...     list(george.favorite_numbers)
    [15, 3]

You can see here that the :class:`float` **3.5** value has been casted into an :class:`int` by the :class:`~sheraf.attributes.simples.IntegerAttribute`.

But you can also nest collections in collection. For instance a :class:`~sheraf.attributes.collections.DictAttribute` can hold another :class:`~sheraf.attributes.collections.DictAttribute`.

.. code-block:: python

    >>> class Cowboy(sheraf.Model):
    ...     table = "cowboy"
    ...     name = sheraf.StringAttribute()
    ...     animal_breeds = sheraf.SmallDictAttribute(
    ...         sheraf.SmallDictAttribute(
    ...             sheraf.StringAttribute()
    ...         )
    ...     )
    ...
    >>> with sheraf.connection(commit=True):
    ...     george = Cowboy.create(
    ...         name="george",
    ...         animal_breeds={
    ...             "horses": {
    ...                  "jolly jumper": "mustang",
    ...             },
    ...         },
    ...     )
    ...     george.animal_breeds["horses"]["jolly jumper"]
    'mustang'

There is no limit on how much attributes can be nested.

Models
------

Models have several ways to reference to other models.

Externals references
~~~~~~~~~~~~~~~~~~~~

The most basic way to reference another model is by using :class:`~sheraf.models.models.ModelAttribute`.

.. code-block:: python

    >>> class Horse(sheraf.Model):
    ...     table = "horse"
    ...     name = sheraf.StringAttribute()
    ...     breed = sheraf.StringAttribute()
    ...
    >>> class Cowboy(sheraf.Model):
    ...     table = "cowboy"
    ...     name = sheraf.StringAttribute()
    ...     horse = sheraf.ModelAttribute(Horse)
    ...
    >>> with sheraf.connection(commit=True):
    ...     jolly = Horse.create(name="Jolly Jumper", breed="mustang")
    ...     george = Cowboy.create(name="George Abitbol", horse=jolly)
    ...     george.horse.name
    'Jolly Jumper'

The **id** of the **Horse** instance will be stored in the **Cowboy** instance.
Accessing to the horse thus makes a second access to the database.

Note that :func:`~sheraf.models.Attribute.create` can make instances for both models.
The inner model should be passed as a dictionnary matching the attribute names to their values:

.. code-block:: python

    >>> with sheraf.connection(commit=True):
    ...     george = Cowboy.create(name="George Abitbol", horse={
    ...         "name": "Jolly Jumper",
    ...         "breed": "mustang",
    ...     })
    ...     george.horse.name
    'Jolly Jumper'

Inlines models
~~~~~~~~~~~~~~

External references to models reach performances limits when scaling. The more the number
of refered models is high, the longer it takes to access one of them. This is due to how
:mod:`BTrees` works.

If the model you refers is very dependant on the referer, you might prefer using a
:class:`~sheraf.attributes.models.InlineModelAttribute` instead.

.. code-block:: python

    >>> class Horse(sheraf.InlineModel):
    ...     name = sheraf.StringAttribute()
    ...     breed = sheraf.StringAttribute()
    ...
    >>> class Cowboy(sheraf.Model):
    ...     table = "cowboy"
    ...     name = sheraf.StringAttribute()
    ...     horse = sheraf.InlineModelAttribute(Horse)
    ...
    >>> with sheraf.connection(commit=True):
    ...     george = Cowboy.create(name="George Abitbol", horse={
    ...         "name": "Jolly Jumper",
    ...         "breed": "mustang",
    ...     })
    ...     george.horse.name
    'Jolly Jumper'

:class:`~sheraf.attributes.models.InlineModelAttribute` works in a very similar way than
:class:`~sheraf.attributes.models.ModelAttribute`. The :class:`~sheraf.models.inline.InlineModel`
is very dependant on its *host* model. It does not have an **id** attribute, an cannot be accessed by
another way than using the :class:`~sheraf.attributes.models.InlineModelAttribute` on its host.

If you need to store several :class:`~sheraf.models.inline.InlineModel`, you might want to use
it in combination with a collection attribute such as :class:`~sheraf.attributes.collections.DictAttribute`
or :class:`~sheraf.attributes.collections.ListAttribute`.

Note that you can define anonymous :class:`~sheraf.models.inline.InlineModel`:

.. code-block:: python

    >>> class Cowboy(sheraf.Model):
    ...     table = "cowboy"
    ...     name = sheraf.StringAttribute()
    ...     horse = sheraf.InlineModelAttribute(sheraf.InlineModel(
    ...         name=sheraf.StringAttribute(),
    ...         breed=sheraf.StringAttribute(),
    ...     ))
    ...
    >>> with sheraf.connection(commit=True):
    ...     george = Cowboy.create(name="George Abitbol", horse={
    ...         "name": "Jolly Jumper",
    ...         "breed": "mustang",
    ...     })
    ...     george.horse.name
    'Jolly Jumper'

Indexed models
~~~~~~~~~~~~~~

:class:`~sheraf.attributes.models.InlineModelAttribute` are great, and using them in combination with
collection attributes gives a good way to handle several of them. However sometimes you may need
more advanced indexation behavior, like with first-level models.

:class:`~sheraf.attributes.models.IndexedModelAttribute` does not store just one model, but a whole
model indexation machine. It handles a :class:`~sheraf.models.AttributeModel` and allows you to use
the :func:`~sheraf.models.indexation.BaseIndexedModel.create`
and :func:`~sheraf.models.indexation.BaseIndexedModel.read` methods from
:class:`~sheraf.models.indexation.BaseIndexedModel`, and take advantages of the :func:`~sheraf.queryset.QuerySet.filter`
and :func:`~sheraf.queryset.QuerySet.order` methods from :class:`~sheraf.queryset.QuerySet`.

.. code-block:: python

    >>> class Horse(sheraf.AttributeModel):
    ...     name = sheraf.StringAttribute().index(primary=True)
    ...     age = sheraf.IntegerAttribute().index(unique=True)
    ...     breed = sheraf.StringAttribute()
    ...
    >>> class Cowboy(sheraf.Model):
    ...     table = "cowboy"
    ...     name = sheraf.StringAttribute()
    ...     horses = sheraf.IndexedModelAttribute(Horse)
    ...
    >>> with sheraf.connection(commit=True):
    ...     george = Cowboy.create(name="George Abitbol")
    ...     jolly = george.horses.create(name="Jolly Jumper", breed="mustang", age=15)
    ...     polly = george.horses.create(name="Polly Pumper", breed="shetland", age=20)
    ...
    ...     george.horses.read("Jolly Jumper").breed
    ...     george.horses.get(age=20).name
    ...     george.horses.count()
    'mustang'
    'Polly Pumper'
    2

Note that the :class:`~sheraf.models.AttributeModel` must have one primary index.

Files
-----

Sheraf offers two ways to store binary files in the database:
:class:`~sheraf.attributes.blobs.BlobAttribute` and
:class:`~sheraf.attributes.files.FileAttribute`.

Blobs
~~~~~

:class:`~sheraf.attributes.blobs.BlobAttribute` makes use of ZODB
:class:`~ZODB.zodb.Blob` objects to store binary files.

.. code-block:: python

    >>> class Cowboy(sheraf.Model):
    ...     table = "cowboy"
    ...     name = sheraf.StringAttribute()
    ...     fax = sheraf.BlobAttribute()
    ...
    >>> with sheraf.connection(commit=True): # doctest: +SKIP
    ...     fax = sheraf.Blob(data=b"Hello George!", filename="fax.txt")
    ...     george = Cowboy.create(name="George", fax=fax)
    ...     george.fax.filename
    ...     george.fax.data
    'fax.txt'
    b'Hello George!'

The file content can either be passed to the :class:`~sheraf.attributes.blobs.Blob` object by the **data** or the **stream** parameter, depending on the format.

As it uses ZODB :class:`~ZODB.zodb.Blob`, files will be removed from the filesystem after a database pack if :func:`~sheraf.attributes.blobs.Blob.delete` is called on the :class:`~sheraf.attributes.blobs.BlobAttribute`.

Files
~~~~~

TODO
