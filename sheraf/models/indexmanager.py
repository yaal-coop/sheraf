import itertools

from BTrees.OOBTree import OOBTree
from sheraf.databases import Database
from sheraf.exceptions import NoDatabaseConnectionException
from sheraf.exceptions import NotConnectedException
from sheraf.exceptions import UniqueIndexException

from ..types import SmallDict


def setdefault(table, key, alternative):
    try:
        return table[key]
    except KeyError:
        return table.setdefault(key, alternative())


class IndexManager:
    root_default = SmallDict
    index_multiple_default = OOBTree

    def __init__(self, details, index_multiple_default=None):
        self.details = details
        if index_multiple_default:
            self.index_multiple_default = index_multiple_default

    def __repr__(self):
        if not self.details:
            return f"<{self.__class__.__name__}>"
        return f"<{self.__class__.__name__} name={self.details.key}>"

    def add_item(self, model, keys=None):
        """
        Sets model instances from a given index .

        :param index: The index where the instances should be set.
        :param keys: The keys to set in the index. If :class:`None`, all
                     the current values of the index for the current model
                     are set.
        """
        if keys is None:
            keys = self.details.get_model_index_keys(model)

        table = self.table()

        for key in keys:
            if self.details.unique:
                self._table_set_unique(table, key, model.mapping)
            else:
                self._table_set_multiple(
                    table, key, model.mapping, model.raw_identifier
                )

    def get_item(self, key, silent_errors=False):
        items = self._get_item(key, silent_errors)

        if not isinstance(items, self.index_multiple_default):
            # TODO: deprecate this and delete it sometimes
            return items

        if self.details.unique:
            return items

        elif items:
            return items.values()

        else:
            return None

    def delete_item(self, model, keys=None, ignore_errors=False):
        """
        Delete model instances from a given index.

        :param index: The index where the instances should be removed.
        :param keys: The keys to remove from the index. If :class:`None`, all
                     the current values of the index for the current model
                     are removed.
        """
        if keys is None:
            keys = self.details.get_model_index_keys(model)

        table = self.table()

        for key in keys:
            if key not in table:
                continue

            try:
                if self.details.unique:
                    self._table_del_unique(table, key, model.mapping)
                else:
                    self._table_del_multiple(
                        table, key, model.mapping, model.raw_identifier
                    )

            except (KeyError, ValueError) as exc:
                if not ignore_errors:
                    raise ValueError(
                        f"{model} not in index '{self.details.key}' key '{key}'"
                    ) from exc

    def update_item(self, model, old_values, new_values, ignore_errors=False):
        if old_values and new_values:
            del_values = old_values - new_values
            add_values = new_values - old_values

            if add_values:
                self.check_item(model, add_values)

            if del_values:
                self.delete_item(model, del_values, ignore_errors)

            if add_values:
                self.add_item(model, add_values)

        elif not old_values:
            self.check_item(model, new_values)
            self.add_item(model, new_values)

        elif not new_values:
            self.delete_item(model, old_values, ignore_errors)

        self._root_check()

    def check_item(self, model, values):
        if not self.details.unique or not self.initialized():
            return

        for value in values:
            if value in self.table():
                raise UniqueIndexException(
                    "The key '{}' is already present in the index '{}'".format(
                        value, self.details.key
                    )
                )

    def _table_del_unique(self, table, index_key, value):
        del table[index_key]

    def _table_del_multiple(self, table, index_key, value, primary_key):
        if isinstance(table[index_key], self.index_multiple_default):
            del table[index_key][primary_key]
            if len(table[index_key]) == 0:
                del table[index_key]
        else:
            # TODO: deprecate this and delete it sometimes
            table[index_key].remove(value)
            if len(table[index_key]) == 0:
                del table[index_key]

    def _table_set_unique(self, table, index_key, value):
        table[index_key] = value

    def _table_set_multiple(self, table, index_key, value, primary_key):
        index_container = setdefault(table, index_key, self.index_multiple_default)

        if isinstance(index_container, self.index_multiple_default):
            index_container[primary_key] = value
        else:
            # TODO: deprecate this and delete it sometimes
            index_container.append(value)

    def _root_check(self):
        if all(not table for table in self.root().values()):
            self.delete_root()


class SimpleIndexManager(IndexManager):
    persistent = None

    def root(self):
        return self.persistent

    def delete_root(self):
        pass

    def initialized(self):
        return self.persistent is not None

    def delete(self):
        del self.persistent[self.details.key]

    def table_initialized(self):
        return self.details.key in self.persistent

    def table(self):
        return setdefault(self.persistent, self.details.key, self.details.mapping)

    def _get_item(self, key, silent_errors=False):
        return self.persistent[self.details.key][key]

    def has_item(self, key):
        return self.persistent[self.details.key].has_key(key)

    def iterkeys(self, reverse=False):
        if reverse:
            return reversed(list(self.table().iterkeys()))
        return self.table().iterkeys()

    def itervalues(self, reverse=False):
        if reverse:
            return reversed(list(self.table().itervalues()))
        return self.table().itervalues()

    def count(self):
        try:
            return len(self.persistent[self.details.key])
        except KeyError:
            return 0


def current_database_name():
    current_name = Database.current_name()
    if not current_name:
        raise NotConnectedException()
    return current_name


class MultipleDatabaseIndexManager(IndexManager):
    def __init__(self, database_name, table, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.database_name = database_name
        self.table_name = table

    def database_root(self, database_name=None):
        database_name = database_name or self.database_name or current_database_name()
        return Database.current_connection(database_name).root()

    def root(self, database_name=None, ignore_errors=True):
        try:
            root = self.database_root(database_name)
        except KeyError as exc:
            raise NoDatabaseConnectionException(database_name) from exc

        if ignore_errors:
            return setdefault(root, self.table_name, self.root_default)

        return root[self.table_name]

    def delete_root(self, database_name=None):
        del self.database_root(database_name)[self.table_name]

    def delete(self):
        try:
            del self.root()[self.details.key]
        except KeyError:
            pass

    def initialized(self, database_name=None):
        for db_name in (database_name, current_database_name()):
            if not db_name:
                continue

            if self.table_name in self.database_root(db_name):
                return True

        return False

    def table(self, database_name=None, ignore_errors=True):
        root = self.root(database_name, ignore_errors)

        if ignore_errors:
            return setdefault(root, self.details.key, self.details.mapping)

        return root[self.details.key]

    def tables(self):
        tables = []
        for db_name in (self.database_name, current_database_name()):
            if not db_name:
                continue

            try:
                tables.append(self.table(db_name, False))
            except KeyError:
                continue

        return tables

    def table_initialized(self):
        for db_name in (self.database_name, current_database_name()):
            if not db_name:
                continue

            try:
                if self.root(db_name, False) and self.details.key in self.root(
                    db_name, False
                ):

                    return True
            except KeyError:
                pass

        return False

    def _get_item(self, key, silent_errors=False):
        last_exc = None
        for table in self.tables():
            try:
                return table[key]
            except KeyError as exc:
                last_exc = exc

        if silent_errors:
            return None

        if last_exc:
            raise last_exc

        raise KeyError

    def has_item(self, key):
        for table in self.tables():
            if table.has_key(key):
                return True

        return False

    def iterkeys(self, reverse=False):
        if reverse:
            return itertools.chain.from_iterable(
                reversed(list(table.iterkeys())) for table in self.tables()
            )

        return itertools.chain.from_iterable(
            table.iterkeys() for table in self.tables()
        )

    def itervalues(self, reverse=False):
        if reverse:
            return itertools.chain.from_iterable(
                reversed(list(table.itervalues())) for table in self.tables()
            )

        return itertools.chain.from_iterable(
            table.itervalues() for table in self.tables()
        )

    def count(self):
        return sum(len(table) for table in self.tables())
