import itertools

import sheraf.types


def table_iterkeys(table, reverse=False):
    try:
        return table.iterkeys(reverse=reverse)
    # TODO: Remove this guard (or just keep it and remove the first lines of this function)
    # on the next compatibility breaking release.
    except TypeError:
        # Some previous stored data may have been OOBTree instead of LargeDict,
        # so the 'reverse' parameter was not available
        keys = table.iterkeys()
        if reverse:
            keys = reversed(list(keys))
        return keys


class IndexManager:
    root_default = sheraf.types.SmallDict
    index_multiple_default = sheraf.types.LargeList

    def __init__(self, index):
        self.index = index

    def add_item(self, model, keys=None):
        """
        Sets model instances from a given index .

        :param index: The index where the instances should be set.
        :param keys: The keys to set in the index. If :class:`None`, all
                     the current values of the index for the current model
                     are set.
        """
        if not keys:
            keys = self.index.values_func(self.index.attribute.read(model))

        table = self.table()

        for key in keys:
            if self.index.unique:
                self._table_set_unique(table, key, model._persistent)
            else:
                self._table_set_multiple(table, key, model._persistent)

    def delete_item(self, model, keys=None):
        """
        Delete model instances from a given index.

        :param index: The index where the instances should be removed.
        :param keys: The keys to remove from the index. If :class:`None`, all
                     the current values of the index for the current model
                     are removed.
        """
        if not keys:
            keys = self.index.values_func(self.index.attribute.read(model))

        table = self.table()

        for key in keys:
            if key not in table:
                continue

            if self.index.unique:
                self._table_del_unique(table, key, model._persistent)
            else:
                self._table_del_multiple(table, key, model._persistent)

    def update_item(self, item, old_keys, new_keys):
        old_values = self.index.values_func(old_keys)
        new_values = self.index.values_func(new_keys)
        del_values = old_values - new_values
        add_values = new_values - old_values

        self.delete_item(item, del_values)
        self.add_item(item, add_values)

    def _table_del_unique(self, table, key, value):
        del table[key]

    def _table_del_multiple(self, table, key, value):
        table[key].remove(value)
        if len(table[key]) == 0:
            del table[key]

    def _table_set_unique(self, table, key, value):
        if key in table:
            raise sheraf.exceptions.UniqueIndexException
        table[key] = value

    def _table_set_multiple(self, table, key, value):
        index_list = table.setdefault(key, self.index_multiple_default())
        index_list.append(value)

    def contains(self, key):
        return any(key in table for table in self.tables())

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

    def iterkeys(self, reverse=False):
        return itertools.chain.from_iterable(
            table_iterkeys(table, reverse) for table in self.tables()
        )

    def count(self):
        """
        :return: the number of instances.

        Using this method is faster than using ``len(MyModel.all())``.
        """
        return sum(len(table) for table in self.tables())


class SimpleIndexManager(IndexManager):
    persistent = None

    def initialized(self):
        return self.persistent is not None

    def table_initialized(self):
        return self.index.key in self.persistent

    def table(self):
        try:
            return self.persistent[self.index.key]
        except KeyError:
            return self.persistent.setdefault(self.index.key, self.index.mapping())

    def tables(self):
        return [self.table()]


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
            del self.root()[self.index.key]
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
            return root[self.index.key]
        except KeyError:
            if not setdefault:
                raise

        return root.setdefault(self.index.key, self.index.mapping())

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
                if self.root(db_name, False) and self.index.key in self.root(
                    db_name, False
                ):
                    return True
            except KeyError:
                pass

        return False
