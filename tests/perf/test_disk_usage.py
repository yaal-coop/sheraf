import os

import transaction

import sheraf


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

            sheraf.Database(filename="tmp/{}.fs".format(Account.__class__.__name__))
            ids = self.build(Account)
            self.check(Account, ids)

            model_size = sum(os.stat(f).st_size for f in self.get_db_files(Model))
            max_size = max(max_size, model_size)
            print((Model.__name__, model_size, "{:.2f}".format(model_size / max_size)))

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
        class Account(sheraf.AutoModel):
            a_attribute = sheraf.SimpleAttribute()
            b_attribute = sheraf.SimpleAttribute()
            c_attribute = sheraf.SimpleAttribute()
            d_attribute = sheraf.SimpleAttribute()

        return Account

    def get_db_files(self, Model):
        name = Model.__class__.__name__
        return [
            "tmp/{}.fs".format(name),
            "tmp/{}.fs.tmp".format(name),
            "tmp/{}.fs.index".format(name),
            "tmp/{}.fs.lock".format(name),
        ]

    def clean(self, Model):
        for f in self.get_db_files(Model):
            try:
                os.remove(f)
            except OSError:
                pass
