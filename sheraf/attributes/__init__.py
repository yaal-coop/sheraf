class ModelLoader(object):
    """
    Loads models from the base in a cache.

    Inherited by most model types
    (``Model[Attribute|List|Set|(Large)Dict]``)
    """

    cache = {}

    def __init__(self, model=None, **kwargs):
        super().__init__(**kwargs)
        self._model = model

    def load_model(self, modelpath):
        # Internal.
        # :param modelpath: namespace of the model to load (eg 'x.y.z')
        # :return: a model class given its path
        if isinstance(modelpath, bytes):
            modelpath = modelpath.decode("utf-8")

        _path = modelpath.split(".")
        _sub_path, _class = ".".join(_path[:-1]), _path[-1]

        _module = __import__(_sub_path, globals(), locals(), [_class], 0)
        # pypy:
        if _module is None:  # pragma: no cover
            raise ImportError(modelpath)

        return getattr(_module, _class)

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
                try:
                    ModelLoader.cache[model] = self.load_model(model)
                except ValueError:
                    raise ImportError

                return ModelLoader.cache[model]

        elif parent and not isinstance(model, type):
            return type(
                "{}.{}".format(parent.__class__.__name__, self.key(parent)),
                (model.__class__,),
                model.attributes,
            )

        else:
            return model
