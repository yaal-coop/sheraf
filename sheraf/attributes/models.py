import inspect

import sheraf
from sheraf.attributes import Attribute
from sheraf.attributes.collections import ListAttribute
from sheraf.attributes.collections import SetAttribute
from sheraf.models.indexation import BaseIndexedModel


class ModelLoader:
    """
    Loads models from the base in a cache.

    Inherited by most model types
    (``Model[Attribute|List|Set|(Large)Dict]``)
    """

    cache = {}

    def __init__(self, model=None, **kwargs):
        super().__init__(**kwargs)
        self._model = model
        modules = [inspect.getmodule(frame[0]) for frame in inspect.stack()]
        self.module_paths = [module.__name__ for module in modules if module]

    def load_model(self, modelpath):
        if isinstance(modelpath, bytes):
            modelpath = modelpath.decode("utf-8")

        path = modelpath.split(".")
        module_path, klass = ".".join(path[:-1]), path[-1]

        module_paths = [module_path] if module_path else self.module_paths

        for module_path in module_paths:
            module = __import__(module_path, globals(), locals(), [klass], 0)

            # pypy:
            if module is None:  # pragma: no cover
                continue

            try:
                return getattr(module, klass)
            except AttributeError:
                pass

        raise ImportError(f"Unable to load model '{klass}'")

    def read(self, parent):
        self.check_model(parent)
        return super().read(parent)

    def write(self, parent, value):
        self.check_model(parent)
        return super().write(parent, value)

    @property
    def model(self):
        self.check_model()
        return self._model

    def check_model(self, parent=None):
        if isinstance(self._model, (list, tuple)):
            self._model = type(self._model)(
                self._check_model(m, parent) for m in self._model
            )
        else:
            self._model = self._check_model(self._model, parent)

    def _check_model(self, model, parent):
        if isinstance(model, (str, bytes)):
            try:
                return ModelLoader.cache[model]
            except KeyError:
                ModelLoader.cache[model] = self.load_model(model)
                return ModelLoader.cache[model]

        elif parent and not isinstance(model, type):
            return type(
                f"{parent.__class__.__name__}.{self.key(parent)}",
                (model.__class__,),
                model.attributes,
            )

        else:
            return model


class AttributeLoader(ModelLoader):
    def __init__(self, attribute=None, **kwargs):
        self._attribute = attribute
        super().__init__(**kwargs)

    def check_attribute(self, attribute_name, parent):
        if attribute_name not in self._model.attributes:
            raise sheraf.SherafException(
                f"'{attribute_name}' is not an attribute of {self._model.__name__}"
            )

        attribute = self._model.attributes[attribute_name]
        if isinstance(attribute, (ListAttribute, SetAttribute)):
            if not isinstance(attribute.attribute, ModelAttribute):
                raise sheraf.SherafException(
                    f"'{self._model.__name__}.{attribute_name}' attribute should hold a 'ModelAttribute' or a 'IndexedModelAttribute' to be referenced by a 'ReverseModelAttribute'"
                )

        elif not isinstance(attribute, (ModelAttribute, IndexedModelAttribute)):
            raise sheraf.SherafException(
                f"'{self._model.__name__}.{attribute_name}' should be a 'ModelAttribute' or a 'IndexedModelAttribute' or a collection of these to be referenced by a 'ReversedModelAttribute'"
            )

        if attribute_name not in self.model.indexes:
            raise sheraf.SherafException(
                f"'{self._model.__name__}.{attribute_name}' should have an index to be referenced by a 'ReversedModelAttribute'"
            )

        return attribute


class ModelAttribute(ModelLoader, Attribute):
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
        kwargs["read_memoization"] = False
        kwargs["write_memoization"] = False
        super().__init__(default=None, model=model, **kwargs)

    def index_keys(self, model):
        """
        By default :class:`~sheraf.attributes.models.ModelAttribute` are indexed on
        their identifier.
        """
        if model is None:
            return {None}

        return {
            (model.table, model.identifier)
            if isinstance(self.model, (tuple, list))
            else model.identifier
        }

    def deserialize(self, value):
        if isinstance(value, tuple):
            table, id_ = value
            model = BaseIndexedModel.from_table(table)
            if model is None:
                self.check_model()
                model = BaseIndexedModel.from_table(table)

        else:
            id_ = value
            model = (
                self.model[0] if isinstance(self.model, (list, tuple)) else self.model
            )
            if model is None:
                self.check_model()
                model = (
                    self.model[0]
                    if isinstance(self.model, (list, tuple))
                    else self.model
                )

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

        elif isinstance(value, tuple):
            return value

        else:
            try:
                return self.model.read(value).identifier
            except sheraf.SherafException:
                return None

    def update(
        self,
        old_value,
        new_value,
        addition=True,
        edition=True,
        deletion=False,
        replacement=False,
    ):
        if replacement or old_value is None or not isinstance(new_value, dict):
            return self.serialize(new_value)

        return old_value.edit(new_value, addition, edition, deletion, replacement)


class ReverseModelAttribute(AttributeLoader, Attribute):
    """
    Inverse reference to a :class:`~sheraf.attributes.models.ModelAttribute`.

    :param model: The :class:`~sheraf.models.Model` to refer to.
    :param attribute: The :class:`~sheraf.attributes.Attribute` in the model to refer to.
        This model must be a :class:`~sheraf.attributes.models.ModelAttribute` or a
        collection of :class:`~sheraf.attributes.models.ModelAttribute`.

    The referenced attribute must be indexed.

    >>> class Cowboy(sheraf.Model):  # doctest: +SKIP
    ...     table = "reverse_cowboys"
    ...     name = sheraf.StringAttribute()
    ...     horse = sheraf.ModelAttribute("Horse").index()
    ...
    >>> class Horse(sheraf.Model):  # doctest: +SKIP
    ...     table = "reverse_horses"
    ...     name = sheraf.StringAttribute()
    ...     cowboy = sheraf.ReverseModelAttribute("Cowboy", "horse")
    ...
    >>> with sheraf.connection():  # doctest: +SKIP
    ...     george = Cowboy.create(name="George")
    ...     horse = Horse.create(name="Jolly", cowboy=george)
    ...     george.horse.name
    "Jolly"

    Collection attributes are also supported:

    >>> class Cowboy(sheraf.Model):  # doctest: +SKIP
    ...     table = "reverse_multicowboys"
    ...     name = sheraf.StringAttribute()
    ...     horses = sheraf.LargeListAttribute(ModelAttribute("Horse").index())
    ...
    >>> class Horse(sheraf.Model):  # doctest: +SKIP
    ...     table = "reverse_multihorses"
    ...     name = sheraf.StringAttribute()
    ...     cowboy = sheraf.ReverseModelAttribute("Cowboy", "horses")
    ...
    >>> with sheraf.connection():  # doctest: +SKIP
    ...     george = Cowboy.create(name="George")
    ...     jolly = Horse.create(name="Jolly", cowboy=george)
    ...     polly = Horse.create(name="Polly", cowboy=george)
    ...     george.horses[0].name
    ...     george.horses[1].name
    "Jolly"
    "Polly"
    """

    def __init__(self, model, attribute, **kwargs):
        kwargs["read_memoization"] = False
        kwargs["write_memoization"] = False
        super().__init__(default=None, model=model, attribute=attribute, **kwargs)

    def read(self, parent):
        self.check_model(parent)
        self.check_attribute(self._attribute, parent)
        search_args = {self._attribute: parent}

        if not self.model.indexes[self._attribute].details.unique:
            return self.model.search(**search_args)

        try:
            return self.model.search(**search_args).get()
        except sheraf.QuerySetUnpackException:
            return None

    def write(self, parent, value):
        self.check_model(parent)
        self.check_attribute(self._attribute, parent)

        self.delete(parent)

        if value is None:
            return None

        if not isinstance(value, (list, set)):
            value = [value]

        # if values are ids, then we should load corresponding models
        checked_values = []
        for v in value:
            if isinstance(v, self.model):
                checked_values.append(v)
            else:
                try:
                    checked_values.append(self.model.read(v))
                except sheraf.ModelObjectNotFoundException:
                    pass

        for referent in checked_values:
            attribute = self.model.attributes[self._attribute]

            if isinstance(attribute, ModelAttribute):
                setattr(referent, self._attribute, parent)

            if isinstance(attribute, sheraf.ListAttribute):
                setattr(
                    referent,
                    self._attribute,
                    getattr(referent, self._attribute) + [parent],
                )

            if isinstance(attribute, sheraf.SetAttribute):
                setattr(
                    referent,
                    self._attribute,
                    getattr(referent, self._attribute) | {parent},
                )

        return checked_values

    def delete(self, parent):
        referents = self.read(parent)

        if referents is None:
            return

        if isinstance(referents, self.model):
            referents = [referents]

        for referent in list(referents):
            attribute = self.model.attributes[self._attribute]

            if isinstance(attribute, ModelAttribute):
                delattr(referent, self._attribute)

            if isinstance(
                attribute,
                sheraf.ListAttribute,
            ):
                new_values = [
                    e for e in getattr(referent, self._attribute) if e != parent
                ]
                setattr(
                    referent,
                    self._attribute,
                    new_values,
                )

            if isinstance(
                attribute,
                sheraf.SetAttribute,
            ):
                new_values = {
                    e for e in getattr(referent, self._attribute) if e != parent
                }
                setattr(
                    referent,
                    self._attribute,
                    new_values,
                )


class InlineModelAttribute(ModelLoader, Attribute):
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

    default_mapping = sheraf.types.SmallDict

    def __init__(self, model=None, **kwargs):
        kwargs.setdefault("default", self.default_mapping)
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


class IndexedModelAttribute(ModelLoader, Attribute):
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

    index_table_default = sheraf.types.SmallDict

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cb_registered = dict()

    def decorate_model(self, parent):
        for index in self.model.indexes.values():
            key = self.key(parent)
            if key not in parent.mapping:
                parent.mapping[key] = self.index_table_default()
            index.persistent = parent.mapping[key]

    def read(self, parent):

        if not self.cb_registered.get(parent):
            self.cb_registered[parent] = True

            @self.model.on_creation
            @self.model.on_deletion
            def update_parent_index(instance):
                old_values = parent.before_index_edition(self)
                yield
                parent.after_index_edition(self, old_values)

        self.decorate_model(parent)
        return self.model

    def write(self, parent, value):
        self.decorate_model(parent)
        if value is not None and not inspect.isclass(value):
            for values_dict in value:
                self.model.create(**values_dict)
        return self.model

    def index_keys(self, model):
        return {instance.raw_identifier for instance in model.all()}

    def search_keys(self, query):
        return {query.raw_identifier if isinstance(query, self.model) else query}
