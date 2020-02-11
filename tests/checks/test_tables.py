import pytest

import sheraf


def test_two_classes_with_same_name_raise_an_exception(sheraf_database):
    NAME = "should_be_unique"

    class OriginalModel(sheraf.Model):
        table = NAME

    expected = r"Table named 'should_be_unique' used twice: .*OriginalModel and .*CopyPastedModel"

    with pytest.raises(sheraf.exceptions.SameNameForTableException, match=expected):

        class CopyPastedModel(sheraf.Model):
            table = NAME
