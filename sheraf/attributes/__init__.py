class ModelLoader(object):
    """Internal class that loads models from the base in a cache.

    Inherited by most model types
    (``Model[Attribute|List|Set|(Large)Dict]``)
    """

    cache = {}

    def __init__(self, model=None, **kwargs):
        super(ModelLoader, self).__init__(**kwargs)
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

    @property
    def model(self):
        if not isinstance(self._model, (str, bytes)):
            return self._model

        try:
            self._model = ModelLoader.cache[self._model]
        except KeyError:
            try:
                ModelLoader.cache[self._model] = self.load_model(self._model)
            except ValueError:
                raise ImportError

            self._model = ModelLoader.cache[self._model]

        return self._model
