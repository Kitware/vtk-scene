from typing import Any

DEFAULT_GROUPS = [
    "sources",
    "representations",
    "views",
    "annotations",
    "luts",
]


class Group:
    """
    Container for objects of the same type belonging into a scene.
    """

    def __init__(self, name):
        """Create a group with a given name

        Args:
            name (str): Name of the group
        """
        self._name = name
        self._content = {}

    @property
    def name(self):
        """Get the current name of the group"""
        return self._name

    @property
    def dict(self):
        """Get the group content as a dict"""
        return self._content

    def keys(self):
        """Return a new view of the group's keys"""
        return self._content.keys()

    def items(self):
        """Return a new view of the group's items ((key, value) pairs)"""
        return self._content.items()

    def values(self):
        """Return a new view of the group's values."""
        return self._content.values()

    def clear(self):
        """Remove all items from the group."""
        self._content.clear()

    def __contains__(self, other):
        other_name = None
        if isinstance(other, AbstractSceneObject):
            other_name = other.name
        elif isinstance(other, str):
            other_name = other

        if other_name is None:
            msg = "Invalid type to check against"
            raise ValueError(msg)

        return other_name in self._content

    def __iter__(self):
        return self._content.__iter__()

    def __setattr__(self, name: str, value):
        if name.startswith("_"):
            self.__dict__[name] = value
        else:
            self._content[name] = value

    def __getattr__(self, name):
        return self._content.get(name)

    def __delattr__(self, name):
        del self._content[name]

    def __getitem__(self, name):
        return self._content.get(name)

    def __setitem__(self, name, value):
        self._content[name] = value

    def __iadd__(self, other):
        if isinstance(other, AbstractSceneObject):
            self._content[other.name] = other
        elif isinstance(other, (list, tuple)) and len(other) == 2:
            name, value = other
            self._content[name] = value
        else:
            msg = f"Invalid type: {type(other)}"
            raise ValueError(msg)
        return self

    def __isub__(self, other):
        name_to_remove = None
        if isinstance(other, AbstractSceneObject):
            name_to_remove = other.name
        elif isinstance(other, str):
            name_to_remove = other
        else:
            msg = f"Invalid type: {type(other)}"
            raise ValueError(msg)

        if name_to_remove in self._content:
            del self._content[other.name]
        else:
            msg = f"'{name_to_remove}' not in group {self._name}"
            raise ValueError(msg)
        return self

    def register(self, name: str, obj: Any):
        """Add or replace object with given name into group

        Args:
            name (str): Name under which the object can be retrieved
            obj (Any): Object to register
        """
        self += (name, obj)

    def unregister(self, name):
        """Remove entry with given name from the group

        Args:
            name (str): name of the object to remove from group
        """
        self -= name


class Scene:
    def __init__(self, name):
        for k in DEFAULT_GROUPS:
            setattr(self, k, Group(k))
        SceneContextManager.get_instance().register_scene(name, self)

    def __getitem__(self, name):
        if name in DEFAULT_GROUPS:
            return getattr(self, name)

        msg = f"'{name}' is not in [{', '.join(DEFAULT_GROUPS)}]"
        raise ValueError(msg)

    def __iadd__(self, other):
        if isinstance(other, AbstractSceneObject):
            if other.group in DEFAULT_GROUPS:
                group = self[other.group]
                group += other
        else:
            msg = f"Invalid argument type {type(other)}"
            raise ValueError(msg)

        return self

    def __isub__(self, other):
        if isinstance(other, AbstractSceneObject):
            if other.group in DEFAULT_GROUPS:
                self[other.group] -= other
        else:
            msg = f"Invalid argument type {type(other)}"
            raise ValueError(msg)

        return self

    def __enter__(self):
        SceneContextManager.get_instance().enter(self)
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        SceneContextManager.get_instance().exit(self)


class SceneContextManager:
    singleton = None

    @classmethod
    def get_instance(cls):
        """
        Returns:
            SceneContextManager: return singleton instance
        """
        if cls.singleton is None:
            cls.singleton = SceneContextManager()

        return cls.singleton

    def __init__(self):
        self._scene_stack = []
        self._scenes = {}

    def enter(self, elem):
        if isinstance(elem, Scene):
            self._scene_stack.append(elem)
        elif hasattr(elem, "scene"):
            self.enter(elem.scene)
        return elem

    def exit(self, elem):
        if (
            len(self._scene_stack)
            and (isinstance(elem, Scene) and elem == self._scene_stack[-1])
        ) or (hasattr(elem, "scene") and elem.scene == self._scene_stack[-1]):
            self._scene_stack.pop()

    def __getitem__(self, name):
        return self._scenes.get(name) or Scene(name)

    def __getattr__(self, name):
        return self._scenes.get(name) or Scene(name)

    @property
    def active_scene(self):
        if len(self._scene_stack):
            return self._scene_stack[-1]
        return None

    def register_scene(self, name, scene):
        self._scenes[name] = scene

    def register(self, elem):
        scene = self.active_scene
        if scene is not None:
            scene += elem

        return scene


class AbstractSceneObject:
    def __init__(self, group, name):
        self._group = group
        self._name = name
        # print(f"register ({group=}, {name=})")
        self._scene = SceneContextManager.get_instance().register(self)

    @property
    def group(self):
        return self._group

    @property
    def name(self):
        return self._name

    @property
    def scene(self):
        return self._scene


DEFAULT_SCENE = SceneContextManager.get_instance().default
SceneManager = SceneContextManager.get_instance()
SceneManager.enter(DEFAULT_SCENE)
