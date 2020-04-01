import sheraf


class InlineModel(sheraf.InlineModel):
    pass


class Model1(sheraf.Model):
    table = "model1_table"

    simple = sheraf.SimpleAttribute(lazy=False)
    my_inline_model = sheraf.InlineModelAttribute(InlineModel, lazy=False)
    my_blob = sheraf.BlobAttribute(lazy=False)
    counter = sheraf.CounterAttribute(lazy=False)
