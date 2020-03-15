from sheraf.attributes.base import BaseAttribute

from .attributes import NamedAttributesModel


class InlineModel(NamedAttributesModel):
    """
    :class:`~sheraf.models.inline.InlineModel` behaves like a regular model, but
    it is not indexed by itself. This has several consequences:
    - The ``table`` attribute is not needed.
    - The :func:`~sheraf.models.base.BaseModel.read` method is not available.
    :class:`~sheraf.models.inline.InlineModel` aims to be used in combination
    with :class:`~sheraf.attributes.models.InlineModelAttribute`.

    >>> class Gun(sheraf.InlineModel):
    ...     nb_bullets = sheraf.IntegerAttribute()
    ...
    >>> class Cowboy(sheraf.Model):
    ...     table = "cowboy"
    ...     name = sheraf.SimpleAttribute()
    ...     gun = sheraf.InlineModelAttribute(Gun)
    ...
    >>> with sheraf.connection(commit=True):
    ...     george = Cowboy.create(
    ...         name="George Abitbol",
    ...         gun=Gun.create(nb_bullets=5),
    ...     )
    ...     assert 5 == george.gun.nb_bullets

    You can manage your own indexation by combining
    :class:`~sheraf.attributes.models.InlineModelAttribute` with a collection
    attribute, like :class:`~sheraf.attributes.collections.DictAttribute`.

    >>> class Gun(sheraf.InlineModel):
    ...     nb_bullets = sheraf.IntegerAttribute()
    ...
    >>> class Cowboy(sheraf.Model):
    ...     table = "cowboy"
    ...     name = sheraf.SimpleAttribute()
    ...     guns = sheraf.LargeDictAttribute(
    ...         sheraf.InlineModelAttribute(Gun)
    ...     )
    ...
    >>> with sheraf.connection(commit=True):
    ...     george = Cowboy.create(
    ...         name="George Abitbol",
    ...         guns = {
    ...             "martha": Gun.create(nb_bullets=6),
    ...             "gretta": Gun.create(nb_bullets=5),
    ...         }
    ...     )
    ...     assert 6 == george.guns["martha"].nb_bullets

    :class:`~sheraf.models.inline.InlineModel` can also be anonymous. To create
    an anonymous model instance, just pass the attributes list as parameter of the
    class.

    >>> class Cowboy(sheraf.Model):
    ...     table = "cowboy"
    ...     name = sheraf.SimpleAttribute()
    ...     horse = sheraf.InlineModelAttribute(
    ...         sheraf.InlineModel(
    ...             name=sheraf.SimpleAttribute()
    ...         )
    ...     )
    ...
    >>> with sheraf.connection(commit=True):
    ...     george = Cowboy.create(horse=dict(name="Jolly Jumper"))
    ...     george.horse.name
    'Jolly Jumper'
    """

    def __init__(self, **kwargs):
        if kwargs:
            self.__class__.attributes = {}

        super().__init__()

        for k, v in kwargs.items():
            if isinstance(v, BaseAttribute):
                v._default_key = k
                self.attributes[k] = v
