"""charge la base de donnees locale

>>> import sheraf
>>> with sheraf.connection(): # doctest: +SKIP
...    pass
"""

import sheraf

if __name__ == "__main__":  # pragma: no cover
    sheraf.Database(zeo=("localhost", 9999))
