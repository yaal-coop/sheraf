Models
======

.. contents::
   :local:

Most of the time we encounter the same model types:

- :class:`~sheraf.models.Model`: They are the main models you use to store your data in the database. They have index capabilities;
- :class:`~sheraf.models.inline.InlineModel`: They are simple models without index capabilities, intended to be used with :class:`~sheraf.attributes.models.InlineModelAttribute`;
- :class:`~sheraf.models.AttributeModel`: They are simple models with index capabilities. They are intended to be used with :class:`~sheraf.attributes.models.IndexedModelAttribute`.

BaseModels
----------

Models are mainly a collection of :class:`~sheraf.attributes.Attibute` with some specificities about how the data is stored.
Each model holds a ``mapping`` attribute, basically a persistent dict, where each :class:`~sheraf.attributes.Attibute` has an entry where its content is stored. The key each attribute use can be set with the attribute ``key`` argument. Generally it is not needed to explicitely set this key because your model will inherit from a class that will do this automatically for you:

- :class:`~sheraf.models.attributes.IntAttributesModel` will use an incrementing :class:`int` key for each attribute;
- :class:`~sheraf.models.attributes.NamedAttributesModel` (from which inherits the commonly used :class:`~sheraf.models.Model`) will use the name attribute as its default key.

This means that if you want to change the name of an attribute in a :class:`~sheraf.models.attributes.NamedAttributesModel`, or change the order of an attribute in an :class:`~sheraf.models.attributes.IntAttributesModel` you will need to explicitely set the key it has before remaning/moving. Else sheraf won't be able to correctly retrieve your data.


Here is an example: First we define models without bothering with setting explicit keys.

.. code-block:: python

    >>> class StringAttributesCowboy(sheraf.NamedAttributesModel, sheraf.UUIDIndexedModel, sheraf.IndexedModel):
    ...     table = "string_attributes_cowboys"
    ...
    ...     name = sheraf.StringAttribute()  # The implicit key is 'name'
    ...     email = sheraf.StringAttribute()  # The implicit key is 'email'
    ...
    >>> class IntAttributesCowboy(sheraf.IntAttributesModel, sheraf.UUIDIndexedModel, sheraf.IndexedModel):
    ...     table = "int_attributes_cowboys"
    ...
    ...     name = sheraf.StringAttribute()  # The implicit key is '0'
    ...     email = sheraf.StringAttribute()  # The implicit key is '1'
    ...
    >>> with sheraf.connection(commit=True):
    ...     george = StringAttributesCowboy.create(name="George", email="george@abitbol.com")
    ...     peter = IntAttributesCowboy.create(name="Peter", email="peter@sheraf.com")

Then we change the name of the ``email`` attribute in ``StringAttributesCowboy``, and we change
the order of the attributes in ``IntAttributesCowboy``. To make previous data still accessible,
we need to update the attribute keys so they stay as they were.

.. code-block:: python

    >>> class StringAttributesCowboy(sheraf.NamedAttributesModel, sheraf.UUIDIndexedModel, sheraf.IndexedModel):
    ...     table = "string_attributes_cowboys"
    ...
    ...     name = sheraf.StringAttribute()
    ...     awesome_email = sheraf.StringAttribute(key="email")
    ...
    >>> class IntAttributesCowboy(sheraf.IntAttributesModel, sheraf.UUIDIndexedModel, sheraf.IndexedModel):
    ...     table = "int_attributes_cowboys"
    ...
    ...     email = sheraf.StringAttribute(key=1)
    ...     name = sheraf.StringAttribute(key=0)
    ...
    >>> with sheraf.connection():
    ...     assert StringAttributesCowboy.read(george.id).awesome_email == "george@abitbol.com"
    ...     assert IntAttributesCowboy.read(peter.id).email == "peter@sheraf.com"

IndexableModel
--------------

The indexation capabilities of the models are held by :class:`~sheraf.models.indexation.BaseIndexedModel`. This class allows the use of methods like :meth:`~sheraf.models.indexation.BaseIndexedModel.read`, :meth:`~sheraf.models.indexation.BaseIndexedModel.read`, :meth:`~sheraf.models.indexation.BaseIndexedModel.search` or :meth:`~sheraf.models.indexation.BaseIndexedModel.filter`. Indexable models needs to be indexed somewhere in the database. Sheraf allows several places for a model to be stored:

- A the top level of the database. This is what does :class:`~sheraf.models.indexation.IndexedModel` (from which inherits the commonly used :class:`~sheraf.models.Model`). :class:`~sheraf.models.indexation.IndexedModel` needs to define a ``table`` attribute to work properly.
- Inside another model mapping. This is what does :class:`~sheraf.models.AttributeModel`, and they must be used with a :class:`~sheraf.attributes.models.IndexedModelAttribute`.

To retrieve an indexed model, it must have at least one :class:`~sheraf.attributes.index.Index` on which to search for. This is why sheraf requires exactly one index which attribute ``primary`` is :class:`True`. Primary index are like regular unique indexes, but it will be used by default in several contexts like the :meth:`~sheraf.models.indexation.BaseIndexedModel.read` method.

Sheraf offers several classes with a primary index already set:

- :class:`~sheraf.models.UUIDIndexedModel` has a `id` primary index which is a :class:`~sheraf.attributes.simples.StringUUIDAttribute`. This means that by default an objet created with this class will have a ``id`` attribute, that will hold a :class:`str` representing a :class:`~uuid.UUID`. The commonly used :class:`~sheraf.models.Model` inherits from this class.
- :class:`~sheraf.models.IntIndexedModel` has a `id` primary index that is an :class:`int` randomly choosen.
- :class:`~sheraf.models.IntOrderedIndexedModel` has a `id` primary index that is an increasing :class:`int`. The first id will be `0`, the second will be `1` and so on.
