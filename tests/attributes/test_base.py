import sheraf


class TestBaseAttribute:
    def test_default_read_and_write_memoization_attribute(self, sheraf_connection):
        attribute = sheraf.BaseAttribute()
        assert attribute.read_memoization is False
        assert attribute.write_memoization is True

    def test_read_and_write_memoization_parameters(self, sheraf_connection):
        attribute = sheraf.BaseAttribute(read_memoization=True, write_memoization=False)
        assert attribute.read_memoization is True
        assert attribute.write_memoization is False

    def test_set_read_memoization_to_true(self, sheraf_connection):
        sheraf.attributes.base.set_read_memoization(True)
        attribute = sheraf.BaseAttribute()
        assert attribute.read_memoization is True
        sheraf.attributes.base.set_read_memoization(False)

    def test_set_write_memoization_to_false(self, sheraf_connection):
        sheraf.attributes.base.set_write_memoization(False)
        attribute = sheraf.BaseAttribute()
        assert attribute.write_memoization is False
        sheraf.attributes.base.set_write_memoization(True)
