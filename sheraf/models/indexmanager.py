import itertools

import sheraf.types


class IndexManager:
    root_default = sheraf.types.SmallDict
    index_multiple_default = sheraf.types.LargeList

    def __init__(self, details):
        self.details = details

    def add_item(self, model, keys=None):
        """
        Sets model instances from a given index .

        :param index: The index where the instances should be set.
        :param keys: The keys to set in the index. If :class:`None`, all
                     the current values of the index for the current model
                     are set.
        """
        if not keys:
            keys = self.details.values_func(self.details.attribute.read(model))

        table = self.table()

        for key in keys:
            if self.details.unique:
                self._table_set_unique(table, key, model.mapping)
            else:
                self._table_set_multiple(table, key, model.mapping)

    def delete_item(self, model, keys=None):
        """
        Delete model instances from a given index.

        :param index: The index where the instances should be removed.
        :param keys: The keys to remove from the index. If :class:`None`, all
                     the current values of the index for the current model
                     are removed.
        """
        if not keys:
            keys = self.details.values_func(self.details.attribute.read(model))

        table = self.table()

        for key in keys:
            if key not in table:
                continue

            if self.details.unique:
                self._table_del_unique(table, key, model.mapping)
            else:
                self._table_del_multiple(table, key, model.mapping)

    def update_item(self, item, old_keys, new_keys):
        old_values = self.details.values_func(old_keys)
        new_values = self.details.values_func(new_keys)

        if old_keys and new_keys:
            del_values = old_values - new_values
            add_values = new_values - old_values

            self.delete_item(item, del_values)
            self.add_item(item, add_values)

        elif not old_keys:
            self.add_item(item, new_values)

        elif not new_keys:
            self.delete_item(item, old_values)

    def _table_del_unique(self, table, key, value):
        del table[key]

    def _table_del_multiple(self, table, key, value):
        table[key].remove(value)
        if len(table[key]) == 0:
            del table[key]

    def _table_set_unique(self, table, key, value):
        if key in table:
            raise sheraf.exceptions.UniqueIndexException(
                "The key '{}' is already present in the index '{}'".format(
                    key, self.details.key
                )
            )
        table[key] = value

    def _table_set_multiple(self, table, key, value):
        index_list = table.setdefault(key, self.index_multiple_default())
        index_list.append(value)


class SimpleIndexManager(IndexManager):
    persistent = None

    def initialized(self):
        return self.persistent is not None

    def table_initialized(self):
        return self.details.key in self.persistent

    def table(self):
        try:
            return self.persistent[self.details.key]
        except KeyError:
            return self.persistent.setdefault(self.details.key, self.details.mapping())

    def get_item(self, key):
        return self.persistent[self.details.key][key]

    def has_item(self, key):
        return self.persistent[self.details.key].has_key(key)

    def iterkeys(self, reverse=False):
        if reverse:
            return reversed(list(self.table().iterkeys()))
        return self.table().iterkeys()

    def count(self):
        try:
            return len(self.persistent[self.details.key])
        except KeyError:
            return 0


def current_database_name():
    current_name = sheraf.Database.current_name()
    if not current_name:
        raise sheraf.exceptions.NotConnectedException()
    return current_name


class MultipleDatabaseIndexManager(IndexManager):
    def __init__(self, database_name, table, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.database_name = database_name
        self.table_name = table

    def database_root(self, database_name=None):
        database_name = database_name or self.database_name or current_database_name()
        return sheraf.Database.current_connection(database_name).root()

    def root(self, database_name=None, setdefault=True):
        root = self.database_root(database_name)
        try:
            return root[self.table_name]
        except KeyError:
            if not setdefault:
                raise
            return root.setdefault(self.table_name, self.root_default())

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

    def table(self, database_name=None, setdefault=True):
        root = self.root(database_name, setdefault)

        try:
            return root[self.details.key]
        except KeyError:
            if not setdefault:
                raise

        return root.setdefault(self.details.key, self.details.mapping())

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

    def get_item(self, key):
        last_exc = None
        for table in self.tables():
            try:
                return table[key]
            except KeyError as exc:
                last_exc = exc

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

    def count(self):
        return sum(len(table) for table in self.tables())
