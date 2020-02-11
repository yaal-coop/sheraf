import sheraf.exceptions
import sheraf.models


class Index(sheraf.models.Model):
    """usage :

    class UserIndex(sheraf.Index):
        table = 'users_index'
        index_dict = sheraf.LargeDictAttribute(sheraf.ModelAttribute(User))
        key = lambda index, model: model.email
    """

    @classmethod
    def add(cls, model):
        return cls._get_instance()._add(model)

    @classmethod
    def get(cls, key):
        return cls._get_instance()._get(key)

    @classmethod
    def delete(cls, model):
        return cls._get_instance()._delete(model)

    @classmethod
    def delete_key(cls, key):
        return cls._get_instance()._delete_key(key)

    @classmethod
    def _get_instance(cls):
        try:
            return next(cls.all())
        except StopIteration:
            return cls.create()

    def _add(self, model):
        self.index_dict[self.key(model)] = model
        return model

    def _get(self, key):
        try:
            return self.index_dict[key]
        except KeyError:
            model = (
                self.attributes["index_dict"].attribute._model
                if hasattr(self.attributes["index_dict"], "attribute")
                else self.attributes["index_dict"].model
            )
            raise sheraf.exceptions.IndexObjectNotFoundException(self, key, model)

    def _delete(self, model):
        self._delete_key(self.key(model))

    def _delete_key(self, key):
        del self.index_dict[key]
