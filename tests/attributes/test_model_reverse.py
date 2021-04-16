import pytest
import sheraf
import tests

# ----------------------------------------------------------------------------
# Unique reference
# ----------------------------------------------------------------------------


class UniqueParent(tests.UUIDAutoModel):
    child = sheraf.ModelAttribute(
        "tests.attributes.test_model_reverse.UniqueParentChild"
    ).index(unique=True)


class UniqueParentChild(tests.UUIDAutoModel):
    parent = sheraf.ReverseModelAttribute(
        "tests.attributes.test_model_reverse.UniqueParent", "child"
    )


def test_unique_string_model_setattr(sheraf_connection):
    mom = UniqueParent.create()
    dad = UniqueParent.create()
    child = UniqueParentChild.create()

    child.parent = mom

    assert mom.child == child
    assert child.parent == mom

    remom = UniqueParent.read(mom.id)
    redad = UniqueParent.read(dad.id)
    rechild = UniqueParentChild.read(child.id)

    assert remom.child == child
    assert rechild.parent == mom

    child.parent = dad
    assert dad.child == child
    assert child.parent == dad

    remom = UniqueParent.read(mom.id)
    redad = UniqueParent.read(dad.id)
    rechild = UniqueParentChild.read(child.id)

    assert redad.child == child
    assert rechild.parent == dad


def test_unique_string_model_create(sheraf_connection):
    mom = UniqueParent.create()
    dad = UniqueParent.create()
    child = UniqueParentChild.create(parent=mom)

    assert mom.child == child
    assert child.parent == mom

    remom = UniqueParent.read(mom.id)
    redad = UniqueParent.read(dad.id)
    rechild = UniqueParentChild.read(child.id)

    assert remom.child == child
    assert rechild.parent == mom

    child.parent = dad
    assert dad.child == child
    assert child.parent == dad

    remom = UniqueParent.read(mom.id)
    redad = UniqueParent.read(dad.id)
    rechild = UniqueParentChild.read(child.id)

    assert redad.child == child
    assert rechild.parent == dad


def test_unique_object_model(sheraf_connection):
    mom = UniqueParent.create()
    dad = UniqueParent.create()
    child = UniqueParentChild.create(parent=mom)

    assert mom.child == child
    assert child.parent == mom

    remom = UniqueParent.read(mom.id)
    redad = UniqueParent.read(dad.id)
    rechild = UniqueParentChild.read(child.id)

    assert remom.child == child
    assert rechild.parent == mom

    child.parent = dad
    assert dad.child == child
    assert child.parent == dad

    remom = UniqueParent.read(mom.id)
    redad = UniqueParent.read(dad.id)
    rechild = UniqueParentChild.read(child.id)

    assert redad.child == child
    assert rechild.parent == dad


def test_unique_delete_child(sheraf_connection):
    parent = UniqueParent.create()
    assert parent.child is None

    child = UniqueParentChild.create(parent=parent)
    assert parent.child == child
    assert child.parent == parent

    child.delete()
    assert parent.child is None
    assert parent.mapping["child"] is None


def test_unique_delete_parent(sheraf_connection):
    parent = UniqueParent.create()
    child = UniqueParentChild.create(parent=parent)

    assert parent.child == child
    assert child.parent == parent

    parent.delete()

    assert child.parent is None


def test_unique_set_parent_none(sheraf_connection):
    parent = UniqueParent.create()
    child = UniqueParentChild.create(parent=parent)

    assert parent.child == child
    assert child.parent == parent

    child.parent = None

    assert child.parent is None
    assert parent.child is None


def test_set_id(sheraf_connection):
    mom = UniqueParent.create()
    dad = UniqueParent.create()
    child = UniqueParentChild.create()

    child.parent = mom.id

    assert mom.child == child
    assert child.parent == mom

    remom = UniqueParent.read(mom.id)
    redad = UniqueParent.read(dad.id)
    rechild = UniqueParentChild.read(child.id)

    assert remom.child == child
    assert rechild.parent == mom

    child.parent = dad.id
    assert dad.child == child
    assert child.parent == dad

    remom = UniqueParent.read(mom.id)
    redad = UniqueParent.read(dad.id)
    rechild = UniqueParentChild.read(child.id)

    assert redad.child == child
    assert rechild.parent == dad


def test_set_bad_id(sheraf_connection):
    mom = UniqueParent.create()
    child = UniqueParentChild.create()

    child.parent = "invalid"

    assert mom.child is None
    assert child.parent is None


# ----------------------------------------------------------------------------
# Multiple references
# ----------------------------------------------------------------------------


class MultipleParent(tests.UUIDAutoModel):
    child = sheraf.ModelAttribute(
        "tests.attributes.test_model_reverse.MultipleParentChild"
    ).index()


class MultipleParentChild(tests.UUIDAutoModel):
    parents = sheraf.ReverseModelAttribute(
        "tests.attributes.test_model_reverse.MultipleParent", "child"
    )


def test_multiple_string_model_setattr(sheraf_connection):
    mom = MultipleParent.create()
    dad = MultipleParent.create()
    child = MultipleParentChild.create()

    child.parents = [mom, dad]

    assert mom.child == child
    assert dad.child == child
    assert set(child.parents) == {mom, dad}

    remom = MultipleParent.read(mom.id)
    redad = MultipleParent.read(dad.id)
    rechild = MultipleParentChild.read(child.id)

    assert remom.child == child
    assert redad.child == child
    assert set(rechild.parents) == {mom, dad}

    child.parents = [dad]
    assert dad.child == child
    assert mom.child is None
    assert set(child.parents) == {dad}

    remom = MultipleParent.read(mom.id)
    redad = MultipleParent.read(dad.id)
    rechild = MultipleParentChild.read(child.id)

    assert redad.child == child
    assert remom.child is None
    assert set(rechild.parents) == {dad}


def test_multiple_string_model_create(sheraf_connection):
    mom = MultipleParent.create()
    dad = MultipleParent.create()
    child = MultipleParentChild.create(parents=[mom, dad])

    assert mom.child == child
    assert dad.child == child
    assert set(child.parents) == {mom, dad}

    remom = MultipleParent.read(mom.id)
    redad = MultipleParent.read(dad.id)
    rechild = MultipleParentChild.read(child.id)

    assert remom.child == child
    assert redad.child == child
    assert set(rechild.parents) == {mom, dad}

    child.parents = [dad]
    assert dad.child == child
    assert mom.child is None
    assert set(child.parents) == {dad}

    remom = MultipleParent.read(mom.id)
    redad = MultipleParent.read(dad.id)
    rechild = MultipleParentChild.read(child.id)

    assert redad.child == child
    assert remom.child is None
    assert set(rechild.parents) == {dad}


def test_multiple_delete_child(sheraf_connection):
    mom = MultipleParent.create()
    dad = MultipleParent.create()

    child = MultipleParentChild.create(parents=[mom, dad])
    assert mom.child == child
    assert dad.child == child
    assert set(child.parents) == {mom, dad}

    child.delete()
    assert mom.child is None
    assert dad.child is None
    assert mom.mapping["child"] is None
    assert dad.mapping["child"] is None


def test_multiple_delete_parent(sheraf_connection):
    mom = MultipleParent.create()
    dad = MultipleParent.create()
    child = MultipleParentChild.create(parents=[mom, dad])

    assert mom.child == child
    assert dad.child == child
    assert set(child.parents) == {mom, dad}

    mom.delete()

    assert set(child.parents) == {dad}
    assert dad.child == child

    dad.delete()

    assert set(child.parents) == set()


# ----------------------------------------------------------------------------
# Errors
# ----------------------------------------------------------------------------


class NoIndexParent(tests.UUIDAutoModel):
    child = sheraf.ModelAttribute("tests.attributes.test_model_reverse.NoIndexChild")


class NoIndexChild(tests.UUIDAutoModel):
    parent = sheraf.ReverseModelAttribute(NoIndexParent, "child")


def test_model_attribute_not_indexed(sheraf_connection):
    parent = NoIndexParent.create()
    with pytest.raises(sheraf.SherafException):
        NoIndexChild.create(parent=parent)


class BadParent(tests.UUIDAutoModel):
    child = sheraf.SimpleAttribute().index()


class BadChild(tests.UUIDAutoModel):
    parent = sheraf.ReverseModelAttribute(BadParent, "child")


def test_not_a_model_attribute(sheraf_connection):
    parent = BadParent.create()
    with pytest.raises(sheraf.SherafException):
        BadChild.create(parent=parent)


class BadAttributeParent(tests.UUIDAutoModel):
    child = sheraf.SimpleAttribute().index()


class BadAttributeChild(tests.UUIDAutoModel):
    parent = sheraf.ReverseModelAttribute(BadAttributeParent, "invalid")


def test_bad_attribute(sheraf_connection):
    parent = BadAttributeParent.create()
    with pytest.raises(sheraf.SherafException):
        BadAttributeChild.create(parent=parent)
