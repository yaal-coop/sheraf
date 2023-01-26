import BTrees
import pytest
import sheraf
import tests


@pytest.mark.parametrize(
    "instance, mapping",
    [
        (sheraf.IntegerAttribute().index(unique=True), BTrees.LOBTree.LOBTree),
        # ( sheraf.IntegerAttribute().index(unique=True, key="my_int"), BTrees.IOBTree.IOBTree)
        (
            sheraf.SimpleAttribute(default=int).index(unique=True),
            BTrees.OOBTree.OOBTree,
        ),
    ],
)
def test_integer_unique_index_creation(sheraf_database, instance, mapping):
    class Model(tests.IntAutoModel):
        my_attribute = instance

    with sheraf.connection(commit=True):
        mfoo = Model.create(my_attribute=22)

    with sheraf.connection() as conn:
        index_table = conn.root()[Model.table]["my_attribute"]
        assert {22} == Model.indexes["my_attribute"].details.get_model_index_keys(mfoo)
        assert {22} == set(index_table)
        assert mfoo.mapping == index_table[22]

        assert isinstance(index_table, mapping)
