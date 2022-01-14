import sheraf


class PasswordAccessor:
    def __init__(self, compare, crypted):
        self.compare = compare
        self.crypted = crypted

    def __str__(self):
        return self.crypted

    def __eq__(self, value):
        return self.compare(value, self.crypted)


class PasswordAttribute(sheraf.Attribute):
    """
    Stores crypted password in the database. Once a password has been crypted,
    it cannot be read back in plain text, however, comparisions are still possible.
    Under the hood, the python :func:`~crypt.crypt` method is used.

    The arguments passed to this attribute are passed to :func:`crypt.mksalt`.

    >>> class Cowboy(sheraf.Model):
    ...     table = "cautious_cowboy"
    ...     email = sheraf.StringAttribute()
    ...     password = sheraf.PasswordAttribute()
    ...
    >>> with sheraf.connection(commit=True):  # doctest: +SKIP
    ...     cowboy = Cowboy.create(email="george@abitbol.com", password="$up3r$3cur3")
    ...     assert cowboy.password == "$up3r$3cur3"
    ...     str(cowboy.password)
    '$6$vQzraMQc3G9Mf/zy$IfPSCPO81IzvGwo6AYoS6K6fen552B22DDz.ARwoxmvyFJ9He7.wVLIWbw0RWEIw/oGUblY9YbGvhwUQbtYEV.'

    """

    def __init__(self, **kwargs):
        self.crypt_args = kwargs
        super().__init__()

    @staticmethod
    def crypt(clear, *args, **kwargs):
        import crypt

        salt = crypt.mksalt(**kwargs)
        return crypt.crypt(clear, salt)

    @staticmethod
    def compare(clear, crypted):
        import crypt

        return crypt.crypt(clear, crypted) == crypted

    def serialize(self, value):
        if value is None:
            return None

        return self.crypt(value, **self.crypt_args)

    def deserialize(self, value):
        if value is None:
            return None

        return PasswordAccessor(self.compare, value)
