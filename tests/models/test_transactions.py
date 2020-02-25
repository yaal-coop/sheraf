import queue
import threading

import pytest
import ZODB.POSException

import sheraf
import sheraf.transactions

from tests.utils import conflict


def test_initial_value():
    _queue = queue.Queue()

    def run(q):
        q.put(sheraf.Database.current_connection())

    thread = threading.Thread(target=run, args=(_queue,))
    thread.start()
    thread.join()
    assert _queue.get(timeout=0.1) is None


class Book(sheraf.AutoModel):
    name = sheraf.SimpleAttribute()


class BookRenamer(threading.Thread):
    def __init__(self, book_id, name):
        super().__init__()
        self.queue = queue.Queue()
        self._book_id = book_id
        self._name = name

    def run(self):
        try:
            self.do_things()
        except Exception as exc:  # pragma: no cover
            self.queue.put(exc)
        else:
            self.queue.put(None)

    def do_things(self):
        def _rename():
            _book = Book.read(self._book_id)
            _book.name = self._name

        with sheraf.connection():
            sheraf.transactions.attempt(_rename, on_failure=None)


def test_threaded_attempt(sheraf_zeo_database):
    nb_threads = 3
    with sheraf.connection(commit=True):
        _book = Book.create()

    _threads = [BookRenamer(_book.id, str(i)) for i in range(nb_threads)]

    for _thread in _threads:
        _thread.start()

    for _thread in _threads:
        _thread.join()
        exc = _thread.queue.get()
        if exc:  # pragma: no cover
            raise exc

    with sheraf.connection():
        _book = _book.read(_book.id)
        assert _book.name in (str(i) for i in range(nb_threads))


def test_attempt(sheraf_database):
    with sheraf.connection():

        def _create():
            _book = Book.create()
            _book.name = "livre"

        sheraf.transactions.attempt(_create, on_failure=None)

    with sheraf.connection():
        [_book] = Book.all()
        assert "livre" == _book.name


def test_args_attempt(sheraf_database):
    with sheraf.connection():

        def _create(arg1, arg2, arg3="", arg4=""):
            return arg1 + arg2 + arg3 + arg4

        result = sheraf.transactions.attempt(
            _create,
            args=("foo", "bar"),
            kwargs={"arg3": "A", "arg4": "B"},
            on_failure=None,
        )

    with sheraf.connection():
        assert "foobarAB" == result


def test_attempt_small_conflict(sheraf_database):
    conflict.reset()
    with sheraf.connection():

        def _create():
            _book = Book.create()
            _book.name = "livre"
            conflict(times=sheraf.transactions.ATTEMPTS - 2)

        sheraf.transactions.attempt(_create, on_failure=None)

    with sheraf.connection():
        [_book] = Book.all()
        assert "livre" == _book.name


def test_attempt_multiple_conflicts(sheraf_database):
    conflict.reset()
    with pytest.raises(ZODB.POSException.ConflictError):
        with sheraf.connection():

            def _create():
                _book = Book.create()
                _book.name = "livre"
                conflict(times=sheraf.transactions.ATTEMPTS)

            sheraf.transactions.attempt(_create, on_failure=None)

    with sheraf.connection():
        assert not list(Book.all())


def test_attempt_exceptions(sheraf_database):
    with pytest.raises(IndexError):
        with sheraf.connection():

            def _create():
                _book = Book.create()
                _book.name = "livre"
                raise IndexError()

            sheraf.transactions.attempt(_create, on_failure=None)

    with sheraf.connection():
        assert not list(Book.all())


def test_commit(sheraf_database):
    with sheraf.connection():

        @sheraf.transactions.commit
        def _create():
            _book = Book.create()
            _book.name = "livre"

        _create()

    with sheraf.connection():
        [_book] = Book.all()
        assert "livre" == _book.name


def test_commit_small_conflict(sheraf_database):
    conflict.reset()
    with sheraf.connection():

        @sheraf.transactions.commit
        def _create():
            _book = Book.create()
            _book.name = "livre"
            conflict(times=sheraf.transactions.ATTEMPTS - 2)

        _create()

    with sheraf.connection():
        [_book] = Book.all()
        assert "livre" == _book.name


def test_commit_multiple_conflicts(sheraf_database):
    conflict.reset()
    with pytest.raises(ZODB.POSException.ConflictError):
        with sheraf.connection():

            @sheraf.transactions.commit
            def _create():
                _book = Book.create()
                _book.name = "livre"
                conflict(times=sheraf.transactions.ATTEMPTS)

            _create()

    with sheraf.connection():
        assert not list(Book.all())


def test_commit_exceptions(sheraf_database):
    with pytest.raises(IndexError):
        with sheraf.connection():

            @sheraf.transactions.commit
            def _create():
                _book = Book.create()
                _book.name = "livre"
                raise IndexError()

            _create()

    with sheraf.connection():
        assert not list(Book.all())
