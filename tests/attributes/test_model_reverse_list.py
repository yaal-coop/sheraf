import pytest
import sheraf
import tests

# ----------------------------------------------------------------------------
# Unique reference
# ----------------------------------------------------------------------------


class UniqueParent(tests.IntAutoModel):
    children = sheraf.LargeListAttribute(
        sheraf.ModelAttribute("tests.attributes.test_model_reverse_list.UniqueChild")
    ).index(unique=True)


class UniqueChild(tests.IntAutoModel):
    parent = sheraf.ReverseModelAttribute(
        "tests.attributes.test_model_reverse_list.UniqueParent", "children"
    )


def test_unique_list_reference(sheraf_connection):
    mom = UniqueParent.create()
    dad = UniqueParent.create()
    child1 = UniqueChild.create(parent=mom)
    child2 = UniqueChild.create(parent=mom)

    assert mom.children == [child1, child2]
    assert child1.parent == mom
    assert child2.parent == mom

    remom = UniqueParent.read(mom.id)
    rechild1 = UniqueChild.read(child1.id)
    rechild2 = UniqueChild.read(child2.id)

    assert remom.children == [child1, child2]
    assert rechild1.parent == mom
    assert rechild2.parent == mom

    child1.parent = dad
    assert dad.children == [child1]
    assert mom.children == [child2]

    remom = UniqueParent.read(mom.id)
    redad = UniqueParent.read(dad.id)
    rechild1 = UniqueChild.read(child1.id)
    rechild2 = UniqueChild.read(child2.id)

    assert remom.children == [child2]
    assert redad.children == [child1]


def test_unique_list_reference_delete_child(sheraf_connection):
    parent = UniqueParent.create()
    child1 = UniqueChild.create(parent=[parent])
    child2 = UniqueChild.create(parent=[parent])

    assert child1 in parent.children
    assert child2 in parent.children
    assert child1.parent == parent
    assert child2.parent == parent

    child1.delete()
    assert parent.children == [child2]
    assert parent.mapping["children"] == [child2.id]

    reparent = UniqueParent.read(parent.id)
    assert reparent.children == [child2]
    assert reparent.mapping["children"] == [child2.id]


# ----------------------------------------------------------------------------
# Multiple reference
# ----------------------------------------------------------------------------


class MultiParent(tests.UUIDAutoModel):
    children = sheraf.LargeListAttribute(
        sheraf.ModelAttribute("tests.attributes.test_model_reverse_list.MultiChild")
    ).index()


class MultiChild(tests.UUIDAutoModel):
    parents = sheraf.ReverseModelAttribute(
        "tests.attributes.test_model_reverse_list.MultiParent", "children"
    )


def test_multiple_list_reference(sheraf_connection):
    mom = MultiParent.create()
    dad = MultiParent.create()
    child1 = MultiChild.create(parents=mom)
    child2 = MultiChild.create(parents=mom)

    assert mom.children == [child1, child2]
    assert child1.parents == [mom]
    assert child2.parents == [mom]

    child1.parents = [dad]
    assert dad.children == [child1]
    assert mom.children == [child2]

    remom = MultiParent.read(mom.id)
    redad = MultiParent.read(dad.id)

    assert redad.children == [child1]
    assert remom.children == [child2]


def test_multiple_list_reference_delete_child(sheraf_connection):
    parent = MultiParent.create()
    child1 = MultiChild.create(parents=[parent])
    child2 = MultiChild.create(parents=[parent])

    assert parent.children == [child1, child2]
    assert child1.parents == [parent]
    assert child2.parents == [parent]

    child1.delete()
    assert parent.children == [child2]
    assert parent.mapping["children"] == [child2.id]

    reparent = MultiParent.read(parent.id)
    assert reparent.children == [child2]
    assert reparent.mapping["children"] == [child2.id]


# ----------------------------------------------------------------------------
# Errors
# ----------------------------------------------------------------------------


class BadParent(tests.UUIDAutoModel):
    child = sheraf.LargeListAttribute(sheraf.SimpleAttribute()).index()


class BadChild(tests.UUIDAutoModel):
    parent = sheraf.ReverseModelAttribute(BadParent, "child")


def test_not_a_model_attribute(sheraf_connection):
    parent = BadParent.create()
    with pytest.raises(sheraf.SherafException):
        BadChild.create(parent=parent)
