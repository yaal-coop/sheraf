import pytest
import sheraf
import tests

# ----------------------------------------------------------------------------
# Unique reference
# ----------------------------------------------------------------------------


class UniqueListParent(tests.IntAutoModel):
    children = sheraf.LargeListAttribute(
        sheraf.ModelAttribute("UniqueListChild")
    ).index(unique=True)


class UniqueListChild(tests.IntAutoModel):
    parent = sheraf.ReverseModelAttribute("UniqueListParent", "children")


def test_unique_list_reference(sheraf_connection):
    mom = UniqueListParent.create()
    dad = UniqueListParent.create()
    child1 = UniqueListChild.create(parent=mom)
    child2 = UniqueListChild.create(parent=mom)

    assert mom.children == [child1, child2]
    assert child1.parent == mom
    assert child2.parent == mom

    remom = UniqueListParent.read(mom.id)
    rechild1 = UniqueListChild.read(child1.id)
    rechild2 = UniqueListChild.read(child2.id)

    assert remom.children == [child1, child2]
    assert rechild1.parent == mom
    assert rechild2.parent == mom

    child1.parent = dad
    assert dad.children == [child1]
    assert mom.children == [child2]

    remom = UniqueListParent.read(mom.id)
    redad = UniqueListParent.read(dad.id)
    rechild1 = UniqueListChild.read(child1.id)
    rechild2 = UniqueListChild.read(child2.id)

    assert remom.children == [child2]
    assert redad.children == [child1]


def test_unique_list_reference_delete_child(sheraf_connection):
    parent = UniqueListParent.create()
    child1 = UniqueListChild.create(parent=[parent])
    child2 = UniqueListChild.create(parent=[parent])

    assert child1 in parent.children
    assert child2 in parent.children
    assert child1.parent == parent
    assert child2.parent == parent

    child1.delete()
    assert parent.children == [child2]
    assert parent.mapping["children"] == [child2.id]

    reparent = UniqueListParent.read(parent.id)
    assert reparent.children == [child2]
    assert reparent.mapping["children"] == [child2.id]


# ----------------------------------------------------------------------------
# Multiple reference
# ----------------------------------------------------------------------------


class MultiListParent(tests.UUIDAutoModel):
    children = sheraf.LargeListAttribute(
        sheraf.ModelAttribute("MultiListChild")
    ).index()


class MultiListChild(tests.UUIDAutoModel):
    parents = sheraf.ReverseModelAttribute("MultiListParent", "children")


def test_multiple_list_reference(sheraf_connection):
    mom = MultiListParent.create()
    dad = MultiListParent.create()
    child1 = MultiListChild.create(parents=mom)
    child2 = MultiListChild.create(parents=mom)

    assert mom.children == [child1, child2]
    assert child1.parents == [mom]
    assert child2.parents == [mom]

    child1.parents = [dad]
    assert dad.children == [child1]
    assert mom.children == [child2]

    remom = MultiListParent.read(mom.id)
    redad = MultiListParent.read(dad.id)

    assert redad.children == [child1]
    assert remom.children == [child2]


def test_multiple_list_reference_delete_child(sheraf_connection):
    parent = MultiListParent.create()
    child1 = MultiListChild.create(parents=[parent])
    child2 = MultiListChild.create(parents=[parent])

    assert parent.children == [child1, child2]
    assert child1.parents == [parent]
    assert child2.parents == [parent]

    child1.delete()
    assert parent.children == [child2]
    assert parent.mapping["children"] == [child2.id]

    reparent = MultiListParent.read(parent.id)
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
