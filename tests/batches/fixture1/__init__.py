import sheraf


class InlineModel(sheraf.InlineModel):
    pass


class DummyModel(sheraf.Model):
    table = "dummymodel_table"
    v = sheraf.SimpleAttribute(lazy_creation=False, default=str)


class Model1(sheraf.Model):
    table = "model1_table"

    simple = sheraf.SimpleAttribute(lazy_creation=False)
    my_inline_model = sheraf.InlineModelAttribute(InlineModel, lazy_creation=False)
    my_blob = sheraf.BlobAttribute(lazy_creation=False)
    counter = sheraf.CounterAttribute(lazy_creation=False)


class Model2(sheraf.Model):
    table = "model2_table"
    simple = sheraf.SimpleAttribute(lazy_creation=False)
    str_indexed = sheraf.SimpleAttribute(lazy_creation=False).index()


class Model2unique(sheraf.Model):
    table = "model2unique_table"
    simple = sheraf.SimpleAttribute(lazy_creation=False)
    str_indexed = sheraf.SimpleAttribute(lazy_creation=False).index(unique=True)


class Model2kunique(sheraf.Model):
    table = "model2kunique_table"
    simple = sheraf.SimpleAttribute(lazy_creation=False)
    str_indexed = sheraf.SimpleAttribute(lazy_creation=False).index(
        unique=True, key="str"
    )


class Model2k(sheraf.Model):
    table = "model2k_table"
    simple = sheraf.SimpleAttribute(lazy_creation=False)
    str_indexed = sheraf.SimpleAttribute(lazy_creation=False).index(key="str")


class Model3(sheraf.Model):
    table = "model3_table"
    simple = sheraf.SimpleAttribute(lazy_creation=False)
    obj_indexed = sheraf.ModelAttribute(DummyModel, lazy_creation=False).index(
        unique=True, values=lambda x: {x.v}
    )


class Model3k(sheraf.Model):
    table = "model3k_table"
    simple = sheraf.SimpleAttribute(lazy_creation=False)
    obj_indexed = sheraf.ModelAttribute(DummyModel, lazy_creation=False).index(
        unique=True, key="obj", values=lambda x: {x.v}
    )
