import pytest
import sheraf


def test_basics():
    counter = sheraf.types.counter.Counter(0)
    assert counter == 0
    assert 0 == counter
    assert counter >= 0
    assert 0 <= counter
    assert counter <= 0
    assert 0 >= counter
    assert counter > -1
    assert -1 < counter
    assert counter < 10
    assert 10 > counter
    assert counter != 9
    assert 9 != counter

    assert 0 == int(counter)
    assert 0.0 == float(counter)
    assert "0" == str(counter)
    assert "<Counter value=0>" == repr(counter)

    counter.set(10)
    assert isinstance(counter, sheraf.types.counter.Counter)
    assert counter == 10
    assert 10 == counter ** 1
    assert 1 == 1 ** counter
    assert 10 == counter % 12
    assert 2 == 12 % counter

    assert 10 == int(counter)
    assert 10 == abs(counter)
    assert 10.0 == float(counter)
    assert "10" == str(counter)
    assert "<Counter value=10>" == repr(counter)
    assert {10} == {counter}


def test_int_math():
    counter = sheraf.types.counter.Counter(2)
    var = 10

    assert 12 == counter + var
    assert 12 == var + counter
    assert -8 == counter - var
    assert 8 == var - counter
    assert 20 == counter * var
    assert 20 == var * counter
    assert 0.2 == counter / var
    assert 5 == var / counter
    assert 0 == counter // var
    assert 5 == var / counter

    counter += 4
    assert counter == 6

    counter -= 4
    assert counter == 2

    counter *= 4
    assert counter == 8

    counter /= 4
    assert counter == 2

    counter //= 2
    assert counter == 1

    var = 10
    counter.set(5)
    assert 5 == counter

    var += counter
    assert 5 == counter
    assert 15 == var

    var -= counter
    assert 5 == counter
    assert 10 == var

    var *= counter
    assert 5 == counter
    assert 50 == var

    var //= counter
    assert 5 == counter
    assert 10 == var

    var /= counter
    assert 5 == counter
    assert 2.0 == var

    class Foo:
        def __add__(self, other):
            return NotImplemented

    with pytest.raises(TypeError):
        counter + Foo()

    with pytest.raises(AttributeError):
        counter += Foo()


def test_float_math():
    counter = sheraf.types.counter.Counter(2.0)
    assert isinstance(counter, sheraf.types.counter.Counter)
    assert isinstance(counter.value, float)

    var = 10.0

    assert 12.0 == counter + var
    assert 12.0 == var + counter
    assert -8.0 == counter - var
    assert 8.0 == var - counter
    assert 20.0 == counter * var
    assert 20.0 == var * counter
    assert 0.2 == counter / var
    assert 5.0 == var / counter
    assert 0.0 == counter // var
    assert 5.0 == var / counter

    counter += 4.0
    assert counter == 6.0

    counter -= 4.0
    assert counter == 2.0

    counter *= 4.0
    assert counter == 8.0

    counter /= 4.0
    assert counter == 2.0

    counter //= 2.0
    assert counter == 1.0

    var = 10.0
    counter.set(5.0)
    assert 5.0 == counter

    var += counter
    assert 5.0 == counter
    assert 15.0 == var

    var -= counter
    assert 5.0 == counter
    assert 10.0 == var

    var *= counter
    assert 5.0 == counter
    assert 50.0 == var

    var //= counter
    assert 5.0 == counter
    assert 10.0 == var

    var /= counter
    assert 5.0 == counter
    assert 2.0 == var


def test_int_float_math():
    counter = sheraf.types.counter.Counter(2)
    assert isinstance(counter, sheraf.types.counter.Counter)
    assert isinstance(counter.value, int)

    counter += 4.0
    assert isinstance(counter.value, float)
    assert counter == 6.0

    counter += 2
    assert isinstance(counter.value, float)
    assert counter == 8.0


def test_counter_math():
    two = sheraf.types.counter.Counter(2)
    counter = sheraf.types.counter.Counter(two)

    assert 4 == two + two
    assert two == 2
    assert counter == 2
    assert counter == two

    counter += two
    assert counter == 4

    counter -= two
    assert counter == 2

    counter *= two
    assert counter == 4

    counter /= two
    assert counter == 2

    counter //= two
    assert counter == 1
