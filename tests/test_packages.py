import importlib.metadata

import vtk_scene as m


def test_version():
    assert importlib.metadata.version("vtk_scene") == m.__version__
