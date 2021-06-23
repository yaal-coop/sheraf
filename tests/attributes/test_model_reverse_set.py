import pytest
import sheraf
import tests

# ----------------------------------------------------------------------------
# Unique reference
# ----------------------------------------------------------------------------


class UniqueSetParent(tests.IntAutoModel):
    children = sheraf.SetAttribute(sheraf.ModelAttribute("UniqueSetChild")).index(
        unique=True
    )


class UniqueSetChild(tests.IntAutoModel):
    parent = sheraf.ReverseModelAttribute("UniqueSetParent", "children")


def test_unique_set_reference(sheraf_connection):
    mom = UniqueSetParent.create()
    dad = UniqueSetParent.create()
    child1 = UniqueSetChild.create(parent=mom)
    child2 = UniqueSetChild.create(parent=mom)

    assert mom.children == {child1, child2}
    assert child1.parent == mom
    assert child2.parent == mom

    remom = UniqueSetParent.read(mom.id)
    rechild1 = UniqueSetChild.read(child1.id)
    rechild2 = UniqueSetChild.read(child2.id)

    assert remom.children == {child1, child2}
    assert rechild1.parent == mom
    assert rechild2.parent == mom

    child1.parent = dad
    assert dad.children == {child1}
    assert mom.children == {child2}

    remom = UniqueSetParent.read(mom.id)
    redad = UniqueSetParent.read(dad.id)
    rechild1 = UniqueSetChild.read(child1.id)
    rechild2 = UniqueSetChild.read(child2.id)

    assert remom.children == {child2}
    assert redad.children == {child1}


def test_unique_set_reference_delete_child(sheraf_connection):
    parent = UniqueSetParent.create()
    child1 = UniqueSetChild.create(parent=[parent])
    child2 = UniqueSetChild.create(parent=[parent])

    assert child1 in parent.children
    assert child2 in parent.children
    assert child1.parent == parent
    assert child2.parent == parent

    child1.delete()
    assert set(parent.mapping["children"]) == {child2.id}
    assert set(parent.children) == {child2}

    reparent = UniqueSetParent.read(parent.id)
    assert set(reparent.mapping["children"]) == {child2.id}
    assert set(reparent.children) == {child2}


# ----------------------------------------------------------------------------
# Multiple reference
# ----------------------------------------------------------------------------


class MultiSetParent(tests.UUIDAutoModel):
    children = sheraf.SetAttribute(sheraf.ModelAttribute("MultiSetChild")).index()


class MultiSetChild(tests.UUIDAutoModel):
    parents = sheraf.ReverseModelAttribute("MultiSetParent", "children")


def test_multiple_set_reference(sheraf_connection):
    mom = MultiSetParent.create()
    dad = MultiSetParent.create()
    child1 = MultiSetChild.create(parents=mom)
    child2 = MultiSetChild.create(parents=mom)

    assert mom.children == {child1, child2}
    assert child1.parents == [mom]
    assert child2.parents == [mom]

    child1.parents = [dad]
    assert dad.children == {child1}
    assert mom.children == {child2}

    remom = MultiSetParent.read(mom.id)
    redad = MultiSetParent.read(dad.id)

    assert redad.children == {child1}
    assert remom.children == {child2}


def test_multiple_set_reference_delete_child(sheraf_connection):
    parent = MultiSetParent.create()
    child1 = MultiSetChild.create(parents=[parent])
    child2 = MultiSetChild.create(parents=[parent])

    assert parent.children == {child1, child2}
    assert child1.parents == [parent]
    assert child2.parents == [parent]

    child1.delete()
    assert set(parent.mapping["children"]) == {child2.id}
    assert parent.children == {child2}

    reparent = MultiSetParent.read(parent.id)
    assert reparent.children == {child2}
    assert set(reparent.mapping["children"]) == {child2.id}


# ----------------------------------------------------------------------------
# Errors
# ----------------------------------------------------------------------------


class BadParent(tests.UUIDAutoModel):
    child = sheraf.SetAttribute(sheraf.SimpleAttribute()).index()


class BadChild(tests.UUIDAutoModel):
    parent = sheraf.ReverseModelAttribute(BadParent, "child")


def test_not_a_model_attribute(sheraf_connection):
    parent = BadParent.create()
    with pytest.raises(sheraf.SherafException):
        BadChild.create(parent=parent)
