import sheraf


class InlineModel(sheraf.InlineModel):
    pass


class Model1(sheraf.Model):
    table = "model1_table"

    simple = sheraf.SimpleAttribute(lazy_creation=False)
    my_inline_model = sheraf.InlineModelAttribute(InlineModel, lazy_creation=False)
    my_blob = sheraf.BlobAttribute(lazy_creation=False)
    counter = sheraf.CounterAttribute(lazy_creation=False)
