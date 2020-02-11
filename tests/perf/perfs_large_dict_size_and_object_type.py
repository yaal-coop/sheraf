import datetime
import os
import random
import shutil
import tempfile
from itertools import chain

import persistent
import transaction

import sheraf


class Test_tel(persistent.Persistent):
    number = ""


class Test_sheraf_tel(sheraf.AutoModel):
    number = sheraf.SimpleAttribute()


class Test_sheraf_tel_in(sheraf.InlineModel):
    number = sheraf.SimpleAttribute()


class Test_sheraf_rep(sheraf.AutoModel):
    tels = sheraf.LargeDictAttribute(sheraf.InlineModelAttribute(Test_sheraf_tel_in))


# cela pourrait être un chargement de contact dans rich-sms
OBJECTS_NUMBERS = 100


class PerfSherafCaseHugeWrite:
    def est_sheraf_perf(self):
        with sheraf.connection():
            for i in range(0, OBJECTS_NUMBERS):
                tel_obj = Test_sheraf_tel.create()
                tel = "33"
                for _ in range(9):
                    tel = tel + str(random.randint(0, 9))
                tel = tel + ";\n"
                tel_obj.number = tel
            transaction.commit()

    def est_sheraf_perf_as_inline(self):
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

    def est_zodb_perf_persistent_mapping(self):
        with sheraf.connection() as c:
            c.root()["parents"] = sheraf.LargeDict()
            for i in range(0, OBJECTS_NUMBERS):
                tel_obj = persistent.mapping.PersistentMapping()
                tel = "33"
                for _ in range(9):
                    tel = tel + str(random.randint(0, 9))
                tel = tel + ";\n"
                tel_obj.number = tel
                c.root()["parents"][i] = tel_obj
            transaction.commit()

    def est_zodb_perf_persistent(self):
        with sheraf.connection() as c:
            c.root()["parents"] = sheraf.LargeDict()
            for i in range(0, OBJECTS_NUMBERS):
                tel_obj = Test_tel()
                tel = "33"
                for _ in range(9):
                    tel = tel + str(random.randint(0, 9))
                tel = tel + ";\n"
                tel_obj.number = tel
                c.root()["parents"][i] = tel_obj
            transaction.commit()


def set_up_database(state):
    state._path = tempfile.mkdtemp()
    sheraf.Database()
    state._old_files_root_dir = sheraf.attributes.files.FILES_ROOT_DIR
    sheraf.attributes.files.FILES_ROOT_DIR = os.path.join(state._path, "files/")


def clear_database(state):
    shutil.rmtree(state._path)
    sheraf.attributes.files.FILES_ROOT_DIR = state._old_files_root_dir
    with sheraf.connection() as c:
        c.root().clear()
        transaction.commit()


class State(object):
    pass


print(
    "test en ajoutant un élément à un dictionnaire de plus en plus gros, un commit à chaque fois"
)
print("on test la résilience à la taille de la base")
print("taille du dict, temps")
num_object = 1000027

points = list(
    chain(
        range(1, 50),
        range(75, 126),
        range(975, 1026),
        range(9975, 10026),
        range(99975, 100026),
        range(199975, 200026),
        range(299975, 300026),
        range(399975, 400026),
        range(499975, 500026),
        range(599975, 600026),
        range(699975, 700026),
        range(799975, 800026),
        range(899975, 900026),
        range(999975, 1000026),
    )
)
flag = False
values = []
state = State()
set_up_database(state)
time = datetime.datetime.now()
with sheraf.connection() as c:
    c.root()["parents"] = sheraf.LargeDict()
    for i in range(0, num_object):
        time = datetime.datetime.now()
        tel_obj = Test_tel()
        tel = "33"
        for _ in range(9):
            tel = tel + str(random.randint(0, 9))
        tel = tel + ";\n"
        tel_obj.number = tel
        c.root()["parents"][i] = tel_obj
        transaction.commit()
        delta = datetime.datetime.now() - time
        if i in points:
            flag = True
            values.append(delta.microseconds)
        else:
            if flag == True:
                flag = False
                print(
                    "med pour les values juste avant %s : %s"
                    % (i, sum(values) / len(values))
                )
                values = []

clear_database(state)
