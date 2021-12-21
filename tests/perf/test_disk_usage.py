import os

import sheraf
import tests
import transaction


class TestDiskStorage:
    def test_disk_usage(self):
        max_size = 0
        for Model in (
            # sheraf.UUIDIndexedDatedNamedAttributesModel,
            sheraf.UUIDIndexedNamedAttributesModel,
            sheraf.IntIndexedNamedAttributesModel,
            sheraf.IntIndexedIntAttributesModel,
        ):
            Account = self.get_Account(Model)
            self.clean(Model)

            sheraf.Database(filename=f"tmp/{Account.__class__.__name__}.fs")
            ids = self.build(Account)
            self.check(Account, ids)

            model_size = sum(os.stat(f).st_size for f in self.get_db_files(Model))
            max_size = max(max_size, model_size)
            print((Model.__name__, model_size, f"{model_size / max_size:.2f}"))

    def build(self, Account):
        with sheraf.connection():
            ids = [self.make_account(i, Account).id for i in range(1000)]
            transaction.commit()
        return ids

    def make_account(self, i, Account):
        a = Account.create()
        a.a_attribute = a.b_attribute = a.c_attribute = a.d_attribute = str(i) * 2
        return a

    def check(self, Account, ids):
        with sheraf.connection():
            for i in ids:
                a = Account.read(i)
                assert a.a_attribute == a.b_attribute == a.c_attribute == a.d_attribute

    def get_Account(self, Model):
        class Account(tests.UUIDAutoModel):
            a_attribute = sheraf.SimpleAttribute()
            b_attribute = sheraf.SimpleAttribute()
            c_attribute = sheraf.SimpleAttribute()
            d_attribute = sheraf.SimpleAttribute()

        return Account

    def get_db_files(self, Model):
        name = Model.__class__.__name__
        return [
            f"tmp/{name}.fs",
            f"tmp/{name}.fs.tmp",
            f"tmp/{name}.fs.index",
            f"tmp/{name}.fs.lock",
        ]

    def clean(self, Model):
        for f in self.get_db_files(Model):
            try:
                os.remove(f)
            except OSError:
                pass
