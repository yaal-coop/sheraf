import sheraf
import tests


class DisabledIndexModel(tests.IntAutoModel):
    enabled = sheraf.SimpleAttribute()
    disabled = sheraf.SimpleAttribute()

    enabled_index = sheraf.Index(enabled, auto=True)
    disabled_index = sheraf.Index(disabled, auto=False)


def test_disabled_index(sheraf_connection):
    foo = DisabledIndexModel.create(enabled="a", disabled="b")

    assert (
        foo.id
        in sheraf_connection.root()[DisabledIndexModel.table]["enabled_index"]["a"]
    )
    assert "disabled_index" not in sheraf_connection.root()[DisabledIndexModel.table]

    assert foo in DisabledIndexModel.filter(enabled="a")
    assert foo in DisabledIndexModel.filter(disabled="b")

    assert foo in DisabledIndexModel.search(enabled_index="a")
    assert foo not in DisabledIndexModel.search(disabled_index="b")
