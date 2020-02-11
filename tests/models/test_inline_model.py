import sheraf


def test_inline_model(sheraf_database):
    class MyInlineModel(sheraf.InlineModel):
        pass

    with sheraf.connection():
        m = MyInlineModel.create()
        assert "<MyInlineModel>" == repr(m)
