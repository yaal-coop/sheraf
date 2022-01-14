import functools
import logging
import random
import time

import sheraf

ATTEMPTS = 5
logger = logging.getLogger(__name__)


def attempt(
    function,
    attempts=ATTEMPTS,
    commit=lambda: True,
    log_exceptions=True,
    args=None,
    kwargs=None,
    also_except=None,
    on_failure=lambda nb_attempt: time.sleep(random.uniform(0, nb_attempt)),
):
    """This method attemps to execute a function several times until no
    ConflictError is encountered.

    :param function: The function to execute.
    :param args: The positionnal arguments to pass to the function.
    :param kwargs: The keyword arguments to pass to the function.
    :param attempts: The number of attempts.
    :param commit: An executable returning a boolean indicating wether to
        commit after executing `function`.
    :param log_exceptions: A boolean indicating wether to log exceptions.
    :param also_except: A tuple containing exception classes. If one of those
        exceptions is catched during the attempt, a new execution will be
        attempted.
    :param on_failure: Callback called after each failed attempt except the
        last one. By default it waits a random time between 0 and `attempts`.
        The callback takes one argument ``nb_attempt``.

    :return: The return value of `function`.

    Example:

    >>> with sheraf.connection():
    ...     try:
    ...         sheraf.attempt(do_amazing_stuff, attempts=5, args=("DANGER",))
    ...     except ZODB.POSException.ConflictError:
    ...         print("Impossible to commit do_amazing_stuff after 5 attempts.")
    ...
    >>> with sheraf.connection():
    ...     try:
    ...         sheraf.attempt(lambda: 1/0, also_except=(ZeroDivisionError,))
    ...     except ZeroDivisionError:
    ...         print("This has very few chances to be successful ¯\\\\_(ツ)_/¯")
    This has very few chances to be successful ¯\\_(ツ)_/¯
    """
    import ZODB.POSException

    args = args or ()
    kwargs = kwargs or {}
    if also_except:
        also_except = also_except if isinstance(also_except, tuple) else (also_except,)
    exception_classes = (ZODB.POSException.ConflictError,) + (also_except or ())
    _exc = Exception

    with sheraf.connection(reuse=True) as connection:
        for x in range(attempts):
            start_time = time.time()
            start_commit_time = None
            try:
                connection.transaction_manager.begin()
                _response = function(*args, **kwargs)

                if commit():
                    start_commit_time = time.time()
                    connection.transaction_manager.commit()
                else:
                    connection.transaction_manager.abort()

                return _response

            except exception_classes as exc:
                # Not so easy to change the message of an exception. Just adding an 'extra_info' field
                # https://stackoverflow.com/questions/6062576/adding-information-to-an-exception
                # https://stackoverflow.com/questions/9157210/how-do-i-raise-the-same-exception-with-a-custom-message-in-python/9157277
                now = time.time()
                execution_time = now - start_time

                if start_commit_time:
                    commit_time = now - start_commit_time
                    exc.extra_info = "Execution n°{} took {:.5f}s of which {:5f}s for the main function and {:5f}s to commit\n".format(
                        x + 1, execution_time, execution_time - commit_time, commit_time
                    )
                else:
                    exc.extra_info = "Execution n°{} took {:.5f}s\n".format(
                        x + 1, execution_time
                    )

                if log_exceptions:
                    extra = {
                        "attempt": x + 1,
                        "exception": exc,
                        "total_time": execution_time,
                        "stack": True,  # Sentry parameter: show full stack
                    }
                    if start_commit_time:
                        extra["commit_time"] = commit_time
                    logger.warning(exc.extra_info, exc_info=True, extra=extra)

                connection.transaction_manager.abort()

                if x != attempts - 1:
                    if on_failure:
                        on_failure(x)

                if x > 0:
                    exc.extra_info += _exc.extra_info

                _exc = exc

            except Exception:
                connection.transaction_manager.abort()
                raise
        raise _exc


def commit(f=None):
    """
    Wrapper shortcut for :func:`~sheraf.transactions.attempt`.

    >>> class Cowboy(sheraf.Model):
    ...     table = "cowboy"
    ...     dead = sheraf.BooleanAttribute(default=False)
    ...
    >>> @sheraf.commit
    ... def fight(winner, loser):
    ...      loser.dead = True
    ...
    >>> with sheraf.connection(commit=True):
    ...     winner = Cowboy.create()
    ...     loser = Cowboy.create()
    ...
    >>> with sheraf.connection():
    ...     fight(winner, loser)
    ...
    >>> with sheraf.connection():
    ...     Cowboy.read(loser.id).dead
    True
    """

    if f is None:
        connection = sheraf.Database.current_connection()
        if not connection:
            raise sheraf.exceptions.NotConnectedException()
        connection.transaction_manager.commit()
        return

    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        return attempt(f, args=args, kwargs=kwargs)

    return wrapper
