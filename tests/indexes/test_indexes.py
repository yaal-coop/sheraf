import pytest

import sheraf


class User(sheraf.AutoModel):
    email = sheraf.SimpleAttribute()


def test_indexes(sheraf_connection):
    class UserIndex(sheraf.Index):
        table = "users_index__call_by_model"
        index_dict = sheraf.LargeDictAttribute(sheraf.ModelAttribute(User))
        key = lambda index, model: model.email

    _user_1 = User.create()
    _user_1.email = "user1@foobar.fr"
    _user_1.save()
    assert _user_1 == UserIndex.add(_user_1)

    _user_2 = User.create()
    _user_2.email = "user2@foobar.fr"
    _user_2.save()
    assert _user_2 == UserIndex.add(_user_2)

    assert _user_1 == UserIndex.get("user1@foobar.fr")
    assert _user_2 == UserIndex.get("user2@foobar.fr")

    UserIndex.delete(_user_1)
    with pytest.raises(sheraf.exceptions.IndexObjectNotFoundException):
        UserIndex.get("user1@foobar.fr")

    UserIndex.delete_key(_user_2.email)
    with pytest.raises(sheraf.exceptions.IndexObjectNotFoundException):
        UserIndex.get("user2@foobar.fr")


def test_string_models(sheraf_connection):
    class UserIndex(sheraf.Index):
        table = "users_index__call_by_string"
        index_dict = sheraf.LargeDictAttribute(
            sheraf.ModelAttribute("tests.indexes.test_indexes.User")
        )
        key = lambda index, model: model.email

    _user_1 = User.create()
    _user_1.email = "user1@foobar.fr"
    _user_1.save()
    assert _user_1 == UserIndex.add(_user_1)

    _user_2 = User.create()
    _user_2.email = "user2@foobar.fr"
    _user_2.save()
    assert _user_2 == UserIndex.add(_user_2)

    assert _user_1 == UserIndex.get("user1@foobar.fr")
    assert _user_2 == UserIndex.get("user2@foobar.fr")

    UserIndex.delete(_user_1)
    with pytest.raises(sheraf.exceptions.IndexObjectNotFoundException):
        UserIndex.get("user1@foobar.fr")

    UserIndex.delete_key(_user_2.email)
    with pytest.raises(sheraf.exceptions.IndexObjectNotFoundException):
        UserIndex.get("user2@foobar.fr")
