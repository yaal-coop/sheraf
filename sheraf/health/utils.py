import importlib
import pkgutil

from sheraf.models.indexation import IndexedModelMetaclass


def import_submodules(*args):
    """Import all submodules of a module, recursively, including subpackages.

    :param *args: packages (name or actual module)
    :type *args: str | module
    :rtype: dict[str, types.ModuleType]
    """
    results = {}
    for package in args:
        if isinstance(package, str):
            package = importlib.import_module(package)

        results[package.__name__] = package

        if not hasattr(package, "__path__"):
            continue

        for path, name, is_pkg in pkgutil.walk_packages(package.__path__):
            if not path.path.startswith(package.__path__[0]):
                continue

            full_name = package.__name__ + "." + name
            if is_pkg:
                results.update(import_submodules(full_name))
            else:
                results[full_name] = importlib.import_module(full_name)

    return results


def discover_models(*args):
    """Discover models in a module.

    :param args: Modules, or module strings.

    :return: A set of models.
    """

    modules = import_submodules(*args)
    result = {
        (path, model)
        for path, model in IndexedModelMetaclass.tables.values()
        if model.__module__ in modules.keys()
    }

    for model in args:
        if isinstance(model, IndexedModelMetaclass):
            result.add(
                (
                    "{}.{}".format(model.__module__, model.__name__),
                    model,
                )
            )

    return result
