import random
import time

import persistent
import sheraf.types
import transaction

OBJECTS_NUMBERS = 10000


class Test_tel(persistent.Persistent):
    number = ""


class Test_tel_3(persistent.Persistent):
    number = ""
    msisdn = ""
    msisdn2 = ""


class Test_sheraf_tel(tests.UUIDAutoModel):
    number = sheraf.SimpleAttribute()


class Test_sheraf_tel_in(sheraf.InlineModel):
    number = sheraf.SimpleAttribute()


class Test_sheraf_tel_in_3(sheraf.InlineModel):
    number = sheraf.SimpleAttribute()
    msisdn = sheraf.SimpleAttribute()
    msisdn2 = sheraf.SimpleAttribute()


class Test_sheraf_rep(tests.UUIDAutoModel):
    tels = sheraf.LargeDictAttribute(sheraf.InlineModelAttribute(Test_sheraf_tel_in))


class Test_sheraf_rep_3(tests.UUIDAutoModel):
    tels = sheraf.LargeDictAttribute(sheraf.InlineModelAttribute(Test_sheraf_tel_in_3))


# cela pourrait être un chargement de contact dans rich-sms
class PerfSherafCaseHugeWrite:
    def sheraf_perf(self, sheraf_database):
        start_time = time.time()
        with sheraf.connection():
            for i in range(0, OBJECTS_NUMBERS):
                tel_obj = Test_sheraf_tel.create()
                tel = "33"
                for _ in range(9):
                    tel = tel + str(random.randint(0, 9))
                tel = tel + ";\n"
                tel_obj.number = tel
            transaction.commit()
        print("--- Ecriture sheraf en %s secondes ---" % (time.time() - start_time))

    def sheraf_perf_as_inline(self, sheraf_database):
        start_time = time.time()
        with sheraf.connection():
            rep = Test_sheraf_rep.create()
            for i in range(0, OBJECTS_NUMBERS):
                tel_obj = Test_sheraf_tel_in.create()
                tel = "33"
                for _ in range(9):
                    tel = tel + str(random.randint(0, 9))
                tel = tel + ";\n"
                tel_obj.number = tel
                rep.tels[i] = tel_obj
            transaction.commit()
        print(
            "--- Ecriture sheraf inline en %s secondes ---" % (time.time() - start_time)
        )

    def zodb_perfmapping_mapping(self, sheraf_database):
        start_time = time.time()
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
        print(
            "--- Ecriture zodb persistent mapping en %s secondes ---"
            % (time.time() - start_time)
        )

    def zodb_perfmapping(self, sheraf_database):
        start_time = time.time()
        with sheraf.connection() as c:
            c.root()["parents"] = sheraf.types.LargeDict()
            for i in range(0, OBJECTS_NUMBERS):
                tel_obj = Test_tel()
                tel = "33"
                for _ in range(9):
                    tel = tel + str(random.randint(0, 9))
                tel = tel + ";\n"
                tel_obj.number = tel
                c.root()["parents"][i] = tel_obj
            transaction.commit()
        print(
            "--- Ecriture zodb persistent object  en %s secondes ---"
            % (time.time() - start_time)
        )

    def zodb_perfmapping_with_one(self, sheraf_database):
        for num_object in [1, 2, 10, 100, 1000, 10000, 100000]:
            start_time = time.time()
            with sheraf.connection() as c:
                c.root()["parents"] = sheraf.types.LargeDict()
                for i in range(0, num_object):
                    tel_obj = Test_tel()
                    tel = "33"
                    for _ in range(9):
                        tel = tel + str(random.randint(0, 9))
                    tel = tel + ";\n"
                    tel_obj.number = tel
                    c.root()["parents"][i] = tel_obj
                transaction.commit()
            print(
                "--- Ecriture zodb persistent object  en %s secondes pour %s objects---"
                % (time.time() - start_time, num_object)
            )

    def zodb_perfmapping_mapping_read_time(self, sheraf_database):
        start_time = time.time()
        with sheraf.connection() as c:
            c.root()["parents"] = sheraf.types.LargeDict()
            for i in range(0, OBJECTS_NUMBERS):
                tel_obj = persistent.mapping.PersistentMapping()
                tel = "33"
                for _ in range(9):
                    tel = tel + str(random.randint(0, 9))
                tel = tel + ";\n"
                tel_obj.number = tel
                tel_obj.msisdn = tel + str(i)
                tel_obj.msisdn2 = tel + str(i * 2)

                c.root()["parents"][i] = tel_obj
            transaction.commit()
        print(
            "--- Ecriture zodb persistent mapping  en %s secondes ---"
            % (time.time() - start_time)
        )
        data = []
        start_time = time.time()
        with sheraf.connection() as c:
            for i in range(0, OBJECTS_NUMBERS):
                tel_obj = c.root()["parents"][i]
                data.append(tel_obj.number)
        print(
            "--- Lecture zodb persistent mapping 1 attr en %s secondes ---"
            % (time.time() - start_time)
        )
        data = []
        start_time = time.time()
        with sheraf.connection() as c:
            for i in range(0, OBJECTS_NUMBERS):
                tel_obj = c.root()["parents"][i]
                data.append(tel_obj.number)
                data.append(tel_obj.msisdn)
                data.append(tel_obj.msisdn2)
        print(
            "--- Lecture zodb persistent mapping 3 attr en %s secondes ---"
            % (time.time() - start_time)
        )

    def zodb_perfmapping_read_time(self, sheraf_database):
        start_time = time.time()
        with sheraf.connection() as c:
            c.root()["parents"] = sheraf.types.LargeDict()
            for i in range(0, OBJECTS_NUMBERS):
                tel_obj = Test_tel_3()
                tel = "33"
                for _ in range(9):
                    tel = tel + str(random.randint(0, 9))
                tel = tel + ";\n"
                tel_obj.number = tel
                tel_obj.msisdn = tel + str(i)
                tel_obj.msisdn2 = tel + str(i * 2)

                c.root()["parents"][i] = tel_obj
            transaction.commit()
        print(
            "--- Ecriture zodb persistent en %s secondes ---"
            % (time.time() - start_time)
        )
        data = []
        start_time = time.time()
        with sheraf.connection() as c:
            for i in range(0, OBJECTS_NUMBERS):
                tel_obj = c.root()["parents"][i]
                data.append(tel_obj.number)
        print(
            "--- Lecture zodb persistent 1 attr en %s secondes ---"
            % (time.time() - start_time)
        )
        data = []
        start_time = time.time()
        with sheraf.connection() as c:
            for i in range(0, OBJECTS_NUMBERS):
                tel_obj = c.root()["parents"][i]
                data.append(tel_obj.number)
                data.append(tel_obj.msisdn)
                data.append(tel_obj.msisdn2)
        print(
            "--- Lecture zodb persistent 3 attr en %s secondes ---"
            % (time.time() - start_time)
        )

    def sheraf_perf_inlinemode_read_time(self, sheraf_database):
        start_time = time.time()
        with sheraf.connection():
            rep = Test_sheraf_rep_3.create()
            for i in range(0, OBJECTS_NUMBERS):
                tel_obj = Test_sheraf_tel_in_3.create()
                tel = "33"
                for _ in range(9):
                    tel = tel + str(random.randint(0, 9))
                tel = tel + ";\n"
                tel_obj.number = tel
                tel_obj.msisdn = tel + str(i)
                tel_obj.msisdn2 = tel + str(i * 2)

                rep.tels[i] = tel_obj
            transaction.commit()
        print(
            "--- Ecriture sheraf inline en %s secondes ---" % (time.time() - start_time)
        )
        data = []
        sheraf.models.count = 0
        start_time = time.time()
        with sheraf.connection():
            rep = next(Test_sheraf_rep_3.all())
            for index, tel_obj in rep.tels:
                # data.append(tel_obj.number)
                data.append(tel_obj.mapping["number"])
        print(
            "--- Lecture sheraf inline 1 attr en %s secondes ---"
            % (time.time() - start_time)
        )
        data = []
        sheraf.models.count = 0
        start_time = time.time()
        with sheraf.connection():
            rep = next(Test_sheraf_rep_3.all())
            for index, tel_obj in rep.tels:
                data.append(tel_obj.number)
        print(
            "--- Lecture sheraf bypass inline 1 attr en %s secondes ---"
            % (time.time() - start_time)
        )
        data = []
        sheraf.models.count = 0
        start_time = time.time()
        with sheraf.connection():
            rep = next(Test_sheraf_rep_3.all())
            for index, tel_obj in rep.tels:
                data.append(tel_obj.mapping["number"])
                data.append(tel_obj.mapping["msisdn"])
                data.append(tel_obj.mapping["msisdn2"])
                # data.append(tel_obj.number)
                # data.append(tel_obj.msisdn)
                # data.append(tel_obj.msisdn2)
        print("Temps cummulé création instances %s " % (sheraf.models.count))
        print(
            "--- Lecture sheraf inline 3 attr en %s secondes ---"
            % (time.time() - start_time)
        )
