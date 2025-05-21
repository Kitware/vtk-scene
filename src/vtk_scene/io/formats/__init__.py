import importlib
import pkgutil
from contextlib import suppress


def get_module_from_suffix(suffix):
    with suppress(ModuleNotFoundError):
        return importlib.import_module(f"vtk_scene.io.formats{suffix}")

    return None


def get_module(name):
    return get_module_from_suffix(f".{name}")


def list_available_modules():
    return [item.name for item in pkgutil.iter_modules(__path__)]


def extract_reader_names():
    names = set()
    for name in list_available_modules():
        m = get_module(name)
        names.update(m.READERS.keys())

    return names


def extract_writer_names():
    names = set()
    for name in list_available_modules():
        m = get_module(name)
        names.update(m.WRITERS.keys())

    return names
