from abc import ABC, abstractmethod

from vtk_scene.core import AbstractSceneObject, Group


class AbstractRepresentation(ABC, AbstractSceneObject):
    representation_count = 0

    @classmethod
    def _next_name(cls):
        cls.representation_count += 1
        return f"representation_{cls.representation_count}"

    def __init__(self, name):
        # internal
        self._views = []

        if name is None:
            name = self._next_name()

        super().__init__(group="representations", name=name)

    @property
    def views(self):
        return self._views

    @abstractmethod
    def add_view(self, view): ...

    @abstractmethod
    def remove_view(self, view): ...


class RepresentationGroup(Group):
    def __init__(self, view):
        super().__init__("representations")
        self._view = view

    def __iadd__(self, other):
        if isinstance(other, AbstractRepresentation):
            other.add_view(self._view)
        return super().__iadd__(other)

    def __isub__(self, other):
        if isinstance(other, AbstractRepresentation):
            other.remove_view(self._view)
        return super().__isub__(other)

    def unregister_all(self):
        for rep in self.values():
            if isinstance(rep, AbstractRepresentation):
                rep.remove_view(self._view)
        super().unregister_all()
