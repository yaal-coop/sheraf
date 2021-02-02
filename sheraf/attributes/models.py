import sheraf
from sheraf.models.indexation import model_from_table
from sheraf.attributes import ModelLoader
from sheraf.attributes.base import BaseAttribute


class ModelAttribute(ModelLoader, BaseAttribute):
    """This attribute references another :class:`~sheraf.models.Model`.

    :param model: The model type to store.
    :type model: :class:`~sheraf.models.Model` or list of :class:`~sheraf.models.Model`

    >>> class Horse(sheraf.Model):
    ...     table = "horse"
    ...     name = sheraf.SimpleAttribute()
    ...
    >>> class Cowboy(sheraf.Model):
    ...     table = "cowboy"
    ...     name = sheraf.SimpleAttribute()
    ...     mount = sheraf.ModelAttribute(Horse)
    ...
    >>> with sheraf.connection(commit=True):
    ...     jolly = Horse.create(name="Jolly Jumper")
    ...     george = Cowboy.create(name="George Abitbol", mount=jolly)
    ...
    ...     george.mount.name
    'Jolly Jumper'

    The referenced model can be dynamically created if its structure is passed through as a dict:

    >>> with sheraf.connection(commit=True):
    ...     peter = Cowboy.create(name="Peter", mount={"name": "Polly Pumper"})
    ...     assert isinstance(peter.mount, Horse)
    ...     peter.mount.name
    'Polly Pumper'

    When the referenced model is deleted, the value of the attribute becomes ``None``.

    >>> with sheraf.connection(commit=True):
    ...     george = Cowboy.read(george.id)
    ...     jolly.delete()
    ...     assert george.mount is None

    Several model classes can be used, but this will be more memory consuming in the database.

    >>> class Pony(sheraf.Model):
    ...     table = "pony"
    ...     name = sheraf.SimpleAttribute()
    ...
    >>> class Cowboy(sheraf.Model):
    ...     table = "cowboy"
    ...     name = sheraf.SimpleAttribute()
    ...     mount = sheraf.ModelAttribute((Horse, Pony))
    ...
    >>> with sheraf.connection(commit=True):
    ...     superpony = Pony.create(name="Superpony")
    ...     peter = Cowboy.create(name="Peter", mount=superpony)

    When several models are set, the first one is considered to be the default model.
    The default model is used when there is a doubt on the read data, or in the case
    of model creation with a dict.
    """

    def __init__(self, model=None, **kwargs):
        if not model:
            raise sheraf.exceptions.SherafException(
                "ModelAttribute requires model parameter."
            )
        super().__init__(default=None, model=model, **kwargs)

    def values(self, model):
        """
        By default :class:`~sheraf.attributes.models.ModelAttribute` are indexed on
        their identifier.
        """
        return {
            (model.table, model.identifier)
            if isinstance(self.model, (tuple, list))
            else model.identifier
        }

    def deserialize(self, value):
        if isinstance(value, tuple):
            table, id_ = value
            model = model_from_table(table)
        else:
            model = (
                self.model[0] if isinstance(self.model, (list, tuple)) else self.model
            )
            id_ = value

        try:
            return model.read(id_)
        except (KeyError, sheraf.exceptions.ModelObjectNotFoundException):
            return None

    def serialize(self, value):
        if value is None:
            return None

        elif isinstance(value, sheraf.IndexedModel):
            return (
                (value.table, value.identifier)
                if isinstance(self.model, (tuple, list))
                else value.identifier
            )

        elif self.model and isinstance(value, dict):
            return self.model.create(**value).identifier

        else:
            return value

    def update(
        self,
        old_value,
        new_value,
        addition=True,
        edition=True,
        deletion=False,
        replacement=False,
    ):
        if replacement or old_value is None:
            return self.serialize(new_value)

        return old_value.edit(new_value, addition, edition, deletion, replacement)


class InlineModelAttribute(ModelLoader, BaseAttribute):
    """:class:`~sheraf.attributes.models.ModelAttribute` behaves like a basic
    model (i.e. have no indexation capability). The child attribute mapping is stored
    in the parent mapping.

    :param model: The model type to store.
    :type model: :class:`~sheraf.models.inline.InlineModel`

    >>> class Horse(sheraf.InlineModel):
    ...     name = sheraf.StringAttribute()
    ...
    >>> class Cowboy(sheraf.Model):
    ...     table = "cowboy_inliner"
    ...     name = sheraf.StringAttribute()
    ...     horse = sheraf.InlineModelAttribute(Horse)
    ...
    >>> with sheraf.connection(commit=True):
    ...     jolly = Horse.create(name="Jolly Jumper")
    ...     george = Cowboy.create(name="George", horse=jolly)
    ...     george.horse.name
    'Jolly Jumper'
    """

    def __init__(self, model=None, **kwargs):
        kwargs.setdefault("default", sheraf.types.SmallDict)
        super().__init__(model=model, **kwargs)

    def deserialize(self, value):
        if value is None:
            return None

        return self.model._decorate(value)

    def serialize(self, value):
        if value is None:
            return None

        elif isinstance(value, sheraf.InlineModel):
            return value.mapping

        elif isinstance(value, dict):
            return self.model.create(**value).mapping

        else:
            return self._default_value(value)

    def update(
        self,
        old_value,
        new_value,
        addition=True,
        edition=True,
        deletion=False,
        replacement=False,
    ):
        if replacement or old_value is None:
            return self.serialize(new_value)

        return old_value.edit(new_value, addition, edition, deletion, replacement)


class IndexedModelAttribute(ModelLoader, BaseAttribute):
    """
    :class:`~sheraf.attributes.models.ModelAttribute` behaves like a classic model,
    including the indexation capabilities. The child attribute mapping and all the
    index mappings are is stored in the parent mapping.

    :param model: The model type to store.
    :type model: :class:`~sheraf.models.AttributeModel`

    .. note:: The :class:`~sheraf.models.AttributeModel` must have a *primary* index.

    >>> class Horse(sheraf.AttributeModel):
    ...     name = sheraf.StringAttribute().index(primary=True)
    ...     size = sheraf.IntegerAttribute().index()
    ...
    >>> class Cowboy(sheraf.Model):
    ...     table = "cowboy_indexer"
    ...     name = sheraf.StringAttribute()
    ...     horses = sheraf.IndexedModelAttribute(Horse)
    ...
    >>> with sheraf.connection(commit=True):
    ...     george = Cowboy.create(name="George Abitbol")
    ...     jolly = george.horses.create(name="Jolly Jumper", size=32)
    ...
    ...     assert jolly == george.horses.read("Jolly Jumper")
    ...     assert jolly in george.horses.search(size=32)
    """

    def read(self, parent):
        for index in self.model.indexes().values():
            key = self.key(parent)
            if key not in parent.mapping:
                parent.mapping[key] = sheraf.types.SmallDict()
            index.persistent = parent.mapping[key]

        return self.model

    def write(self, parent, value):
        model = self.read(parent)
        for values_dict in value:
            model.create(**values_dict)
        return model
