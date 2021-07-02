from sheraf.health.utils import discover_models


def test_model_discovery_module():
    from . import fixture1

    discovery = discover_models(fixture1)

    from .fixture1 import Model1
    from .fixture1.subdirectory.model2 import Model2

    assert ("tests.health.fixture1.Model1", Model1) in discovery
    assert ("tests.health.fixture1.subdirectory.model2.Model2", Model2) in discovery


def test_model_discovery_model_path():
    discovery = discover_models("tests.health.fixture1.Model1")

    from .fixture1 import Model1
    from .fixture1.subdirectory.model2 import Model2

    assert ("tests.health.fixture1.Model1", Model1) in discovery
    assert ("tests.health.fixture1.subdirectory.model2.Model2", Model2) not in discovery


def test_model_discovery_with_model():
    from .fixture1 import Model1

    discovery = discover_models(Model1)

    assert ("tests.health.fixture1.Model1", Model1) in discovery
