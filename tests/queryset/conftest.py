import pytest
import sheraf.models


class Cowboy(sheraf.IntOrderedNamedAttributesModel):
    table = "my_model_queryset"
    age = sheraf.IntegerAttribute()
    name = sheraf.StringAttribute(default="John Doe")
    email = sheraf.StringAttribute().index(unique=True)
    genre = sheraf.StringAttribute(default="M")
    size = sheraf.IntegerAttribute().index()


@pytest.fixture
def m0():
    return Cowboy.create(age=30, name="Peter", size=180, email="peter@peter.com")


@pytest.fixture
def m1():
    return Cowboy.create(
        age=50, name="George Abitbol", size=170, email="george@george.com"
    )


@pytest.fixture
def m2():
    return Cowboy.create(age=30, name="Steven", size=160, email="steven@steven.com")


@pytest.fixture
def m3():
    return Cowboy.create(age=30, name="Dave", size=170, email="dave@dave.com")
