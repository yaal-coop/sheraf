import datetime
import random

import persistent
import transaction

import sheraf
import sheraf.types

OBJECTS_NUMBERS = 100_000


class ZODBPersistent(persistent.Persistent):
    number = ""


class Y_ZODBModel(sheraf.AutoModel):
    number = sheraf.SimpleAttribute()


class Y_ZODBInlineModel(sheraf.InlineModel):
    number = sheraf.SimpleAttribute()


class Y_ZODBModelWithInlineAttribute(sheraf.AutoModel):
    tels = sheraf.LargeDictAttribute(sheraf.InlineModelAttribute(Y_ZODBInlineModel))


# cela pourrait être un chargement de contact dans rich-sms
class PerfSherafCaseHugeWrite:
    def test_sheraf_perf(self, sheraf_database):
        time = datetime.datetime.now()
        with sheraf.connection():
            for i in range(0, OBJECTS_NUMBERS):
                tel_obj = Y_ZODBModel.create()
                tel = "33"
                for _ in range(9):
                    tel = tel + str(random.randint(0, 9))
                tel = tel + ";\n"
                tel_obj.number = tel
            transaction.commit()
        time2 = datetime.datetime.now()
        print(
            "%s , %s , %s"
            % (OBJECTS_NUMBERS, time2 - time, (time2 - time) / OBJECTS_NUMBERS)
        )

    def test_sheraf_perf_as_inline(self, sheraf_database):
        with sheraf.connection():
            rep = Y_ZODBModelWithInlineAttribute.create()
            for i in range(0, OBJECTS_NUMBERS):
                tel_obj = Y_ZODBInlineModel.create()
                tel = "33"
                for _ in range(9):
                    tel = tel + str(random.randint(0, 9))
                tel = tel + ";\n"
                tel_obj.number = tel
                rep.tels[i] = tel_obj
            transaction.commit()

    def test_zodb_perfmapping_mapping(self, sheraf_database):
        with sheraf.connection() as c:
            c.root()["parents"] = sheraf.types.LargeDict()
            for i in range(0, OBJECTS_NUMBERS):
                tel_obj = persistent.mapping.PersistentMapping()
                tel = "33"
                for _ in range(9):
                    tel = tel + str(random.randint(0, 9))
                tel = tel + ";\n"
                tel_obj.number = tel
                c.root()["parents"][i] = tel_obj
            transaction.commit()

    def test_zodb_perfmapping(self, sheraf_database):
        with sheraf.connection() as c:
            c.root()["parents"] = sheraf.types.LargeDict()
            for i in range(0, OBJECTS_NUMBERS):
                tel_obj = ZODBPersistent()
                tel = "33"
                for _ in range(9):
                    tel = tel + str(random.randint(0, 9))
                tel = tel + ";\n"
                tel_obj.number = tel
                c.root()["parents"][i] = tel_obj
            transaction.commit()
