import threading

import transaction

import sheraf


class Child(sheraf.InlineModel):
    nom = sheraf.SimpleAttribute()
    a1 = sheraf.SimpleAttribute()
    a2 = sheraf.SimpleAttribute()
    a3 = sheraf.SimpleAttribute()

    @classmethod
    def create(cls, val):
        model = super().create()
        model.nom = val
        model.a1 = val
        model.a2 = val
        model.a3 = val
        model.check(val)
        return model

    def check(self, key):
        assert key == self.nom == self.a1 == self.a2 == self.a3

    def __eq__(self, other):
        return (
            self.nom == other.nom
            and self.a1 == other.a1
            and self.a2 == other.a2
            and self.a3 == other.a3
        )


class Parent(sheraf.AutoModel):
    sons = sheraf.LargeDictAttribute(sheraf.InlineModelAttribute(Child))
    daughters = sheraf.SmallListAttribute(sheraf.InlineModelAttribute(Child))


LENGTH = 10000
NUMBER_OF_THREADS = 4


class TestIterations:
    def test_inline_model_dict(self, sheraf_database):
        with sheraf.connection():
            _parent = Parent.create()
            for i in range(LENGTH):
                _parent.sons[i] = Child.create(i)
            transaction.commit()

        class Reader(threading.Thread):
            def __init__(self):
                super().__init__()
                self.failed = False

            def run(self):
                with sheraf.connection():
                    _parent = next(Parent.all())
                    for key, son in _parent.sons:
                        try:
                            son.check(key)
                        except:
                            self.failed = True

        readers = [Reader() for i in range(NUMBER_OF_THREADS)]
        [r.start() for r in readers]

        [r.join() for r in readers]
        assert not any((r.failed for r in readers))


class TestZip:
    def test(self, sheraf_database):
        with sheraf.connection():
            _p1 = Parent.create()
            _p2 = Parent.create()
            for i in range(LENGTH):
                _p1.daughters.append(Child.create(i))
                _p2.daughters.append(Child.create(i))
            transaction.commit()

        class Reader(threading.Thread):
            def __init__(self):
                super().__init__()
                self.failed = False

            def run(self):
                with sheraf.connection():
                    [_p1, _p2] = Parent.all()
                    for _d1, _d2 in zip(_p1.daughters, _p2.daughters):
                        if not _d1 == _d2:
                            self.failed = True

        readers = [Reader() for i in range(NUMBER_OF_THREADS)]
        [r.start() for r in readers]

        [r.join() for r in readers]
        assert not any((r.failed for r in readers))
