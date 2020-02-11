import pytest

import sheraf
import sheraf.models


class Cowboy(sheraf.models.IntOrderedNamedAttributesModel):
    table = "my_model_queryset"
    age = sheraf.IntegerAttribute()
    name = sheraf.SimpleAttribute(default="John Doe")
    genre = sheraf.SimpleAttribute(default="M")
    size = sheraf.IntegerAttribute()


@pytest.fixture
def m0():
    return Cowboy.create(age=30, name="Peter", size=180)


@pytest.fixture
def m1():
    return Cowboy.create(age=50, name="George Abitbol", size=170)


@pytest.fixture
def m2():
    return Cowboy.create(age=30, name="Steven", size=160)


@pytest.fixture
def m3():
    return Cowboy.create(age=30, name="Dave", size=170)
