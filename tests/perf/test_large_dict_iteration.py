import time

import sheraf
import tests

DICT_SIZE = 10**5


class TestLargeDict(sheraf.testing.TestCase):
    def test_iteration_integer(self):
        huge_dict = sheraf.types.LargeDict({i: i for i in range(DICT_SIZE)})

        start_classical = time.perf_counter()
        for v in list(huge_dict.values())[5000:6000]:
            v
        duration_classical = time.perf_counter() - start_classical

        start_enhanced = time.perf_counter()
        for v in huge_dict[5000:6000]:
            v
        duration_enhanced = time.perf_counter() - start_enhanced

        assert duration_enhanced < duration_classical

    def test_iteration_integer_backward(self):
        huge_dict = sheraf.types.LargeDict({i: i for i in range(DICT_SIZE)})

        start_classical = time.perf_counter()
        for v in list(huge_dict.values())[5000:6000:-1]:
            v
        duration_classical = time.perf_counter() - start_classical

        start_enhanced = time.perf_counter()
        for v in huge_dict[5000:6000:-1]:
            v
        duration_enhanced = time.perf_counter() - start_enhanced

        assert duration_enhanced < duration_classical

    def test_iteration_integer_complete_backward(self):
        huge_dict = sheraf.types.LargeDict({i: i for i in range(DICT_SIZE)})

        start_classical = time.perf_counter()
        for v in reversed(huge_dict.values()):
            v
        duration_classical = time.perf_counter() - start_classical

        start_enhanced = time.perf_counter()
        for v in huge_dict[::-1]:
            v
        duration_enhanced = time.perf_counter() - start_enhanced

        assert abs(duration_enhanced) - abs(duration_classical) < 1

    def test_model(self):
        class FoobarModel(tests.UUIDAutoModel):
            lorem = sheraf.SimpleAttribute()

        with sheraf.connection(commit=True):
            for _ in range(DICT_SIZE):
                FoobarModel.create()

        with sheraf.connection():
            start_classical = time.perf_counter()
            for v in reversed(list(FoobarModel.all())):
                v
            duration_classical = time.perf_counter() - start_classical

        with sheraf.connection():
            start_enhanced = time.perf_counter()
            for v in FoobarModel.order(sheraf.DESC):
                v
            duration_enhanced = time.perf_counter() - start_enhanced

        assert duration_enhanced < duration_classical
