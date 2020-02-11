import sheraf
from sheraf.attributes import ModelLoader
from sheraf.attributes.base import BaseAttribute


class ModelAttribute(ModelLoader, BaseAttribute):
    """This attribute references another :class:`~sheraf.models.Model`.

    >>> class Horse(sheraf.Model):
    ...     table = "horse"
    ...     name = sheraf.SimpleAttribute()
    ...
    >>> class Cowboy(sheraf.Model):
    ...     table = "cowboy"
    ...     name = sheraf.SimpleAttribute()
    ...     horse = sheraf.ModelAttribute(Horse)
    ...
    >>> with sheraf.connection(commit=True):
    ...     jolly = Horse.create(name="Jolly Jumper")
    ...     george = Cowboy.create(name="George Abitbol", horse=jolly)
    ...
    ...     george.horse.name
    'Jolly Jumper'

    The referenced model can be dynamically created if its structure is passed through as a dict:

    >>> with sheraf.connection(commit=True):
    ...     peter = Cowboy.create(name="Peter", horse={"name": "Polly Pumper"})
    ...     assert isinstance(peter.horse, Horse)
    ...     peter.horse.name
    'Polly Pumper'

    When the referenced model is deleted, the value of the attribute becomes ``None``.

    >>> with sheraf.connection(commit=True):
    ...     george = Cowboy.read(george.id)
    ...     jolly.delete()
    ...     assert george.horse is None
    """

    def __init__(self, model=None, **kwargs):
        super(ModelAttribute, self).__init__(default=None, model=model, **kwargs)

    def deserialize(self, value):
        try:
            return self.model.read(value)
        except (KeyError, sheraf.exceptions.ModelObjectNotFoundException):
            return None

    def serialize(self, value):
        if value is None:
            return None

        elif isinstance(value, sheraf.IndexedModel):
            return value.id

        elif isinstance(value, dict):
            return self.model.create(**value).id

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
