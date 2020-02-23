import sheraf
import sys

from unittest.mock import patch


def assert_filter_queryset(qs, is_indexed=False):
    with patch(
        "sheraf.queryset.QuerySet._init_indexed_iterator"
    ) as indexed_iterator_method:
        list(qs)
        if not is_indexed:
            assert not indexed_iterator_method.called
        elif sys.version_info >= (3, 6):
            indexed_iterator_method.assert_called_once()


def test_temp_canonic_index(sheraf_database):
    class Cowboy(sheraf.AutoModel):
        boot_brand = sheraf.SimpleAttribute().index()

    with sheraf.connection(commit=True):
        Cowboy.create(boot_brand="cowboot")

    with sheraf.connection():
        qs = Cowboy.filter(boot_brand="cowboot")
        assert_filter_queryset(qs, is_indexed=True)


def test_temp_canonic_no_index(sheraf_database):
    class Cowboy(sheraf.AutoModel):
        boot_brand = sheraf.SimpleAttribute()

    with sheraf.connection(commit=True):
        Cowboy.create(boot_brand="cowboot")

    with sheraf.connection():
        qs = Cowboy.filter(boot_brand="booboot")
        assert_filter_queryset(qs, is_indexed=False)


def test_de_indexed_one_attr_and_do_not_recreate_instance(sheraf_database):
    class Cowboy(sheraf.AutoModel):
        boot_brand = sheraf.SimpleAttribute().index()

    with sheraf.connection(commit=True):
        Cowboy.create(boot_brand="cowboot")
        Cowboy.create(boot_brand="booboot")

    class Cowboy(sheraf.AutoModel):
        boot_brand = sheraf.SimpleAttribute()

    with sheraf.connection() as conn:
        assert len(conn.root()["cowboy"]["boot_brand"]) == 2
        qs = Cowboy.filter(boot_brand="booboot")
        assert_filter_queryset(qs, is_indexed=False)


def test_de_indexed_and_lazify_one_attr_and_do_not_recreate_instance(sheraf_database):
    class Cowboy(sheraf.AutoModel):
        boot_brand = sheraf.SimpleAttribute().index()

    with sheraf.connection(commit=True):
        Cowboy.create(boot_brand="cowboot")
        Cowboy.create(boot_brand="booboot")

    class Cowboy(sheraf.AutoModel):
        # TODO: This should be forbidden....Check it?
        boot_brand = sheraf.SimpleAttribute(lazy_creation=True)

    with sheraf.connection():
        qs = Cowboy.filter(boot_brand="booboot")
        assert_filter_queryset(qs, is_indexed=False)


def test_de_indexed_one_attr_and_recreate_instance(sheraf_database):
    class Cowboy(sheraf.AutoModel):
        boot_brand = sheraf.SimpleAttribute().index()

    with sheraf.connection(commit=True):
        Cowboy.create(boot_brand="cowboot")
        Cowboy.create(boot_brand="booboot")

    class Cowboy(sheraf.AutoModel):
        boot_brand = sheraf.SimpleAttribute()

    with sheraf.connection(commit=True):
        Cowboy.create(boot_brand="booboot")

    with sheraf.connection() as conn:
        assert "cowboot" in conn.root()["cowboy"]["boot_brand"]
        assert len(conn.root()["cowboy"]["boot_brand"]) == 2
        qs = Cowboy.filter(boot_brand="booboot")
        assert len(list(qs)) == 2
        assert_filter_queryset(qs, is_indexed=False)


def test_de_indexed_one_of_two_attr(sheraf_database):
    class Cowboy(sheraf.AutoModel):
        boot_brand = sheraf.SimpleAttribute().index()
        # TODO: ask Eloi about usability of index() with values/filter without lambda
        sock_brand = sheraf.SimpleAttribute().index()

    with sheraf.connection(commit=True):
        Cowboy.create(boot_brand="cowboot", sock_brand="one")
        Cowboy.create(boot_brand="booboot", sock_brand="one")
        Cowboy.create(boot_brand="reboot", sock_brand="two")

    class Cowboy(sheraf.AutoModel):
        boot_brand = sheraf.SimpleAttribute()
        sock_brand = sheraf.SimpleAttribute().index()

    with sheraf.connection(commit=True):
        Cowboy.create(boot_brand="booboot")

    with sheraf.connection() as conn:
        assert len(conn.root()["cowboy"]["boot_brand"]) == 3
        assert len(list(Cowboy.filter(sock_brand="one"))) == 2
        qs_boot = Cowboy.filter(boot_brand="booboot")
        assert_filter_queryset(qs_boot, is_indexed=False)
        qs_sock = Cowboy.filter(sock_brand="one")
        assert_filter_queryset(qs_sock, is_indexed=True)
