import sheraf.exceptions
import sheraf.types
from sheraf.attributes import ModelLoader
from sheraf.attributes.base import BaseAttribute


class InlineModelAttribute(ModelLoader, BaseAttribute):
    """Class for defining attributes whose value is stored in their owner
    object as a dictionary, as opposed to ModelAttributes where the
    corresponding object 'id' is stored instead.

    Use this class (1) to faster access the objects referenced by this
    attribute (2) to encapsulate data for which direct access through
    tables is not preferred.

    :class:`~sheraf.attributes.inline.InlineModelAttribute` should refer to
    :class:`~sheraf.models.inline.InlineModel`.
    """

    def __init__(self, model=None, **kwargs):
        kwargs.setdefault("default", sheraf.types.SmallDict)
        super(InlineModelAttribute, self).__init__(model=model, **kwargs)

    def deserialize(self, value):
        if value is None:
            return None

        return self.model._decorate(value)

    def serialize(self, value):
        if value is None:
            return None

        elif isinstance(value, sheraf.InlineModel):
            return value._persistent

        elif isinstance(value, dict):
            return self.model.create(**value)._persistent

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
