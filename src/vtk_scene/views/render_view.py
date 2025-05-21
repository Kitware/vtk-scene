import vtkmodules.vtkRenderingOpenGL2  # noqa: F401
from vtkmodules.vtkInteractionStyle import vtkInteractorStyleSwitch  # noqa: F401
from vtkmodules.vtkInteractionWidgets import vtkOrientationMarkerWidget
from vtkmodules.vtkRenderingAnnotation import vtkAxesActor
from vtkmodules.vtkRenderingCore import (
    vtkRenderer,
    vtkRenderWindow,
    vtkRenderWindowInteractor,
)

from vtk_scene import representations
from vtk_scene.core import AbstractSceneObject
from vtk_scene.representations.core import RepresentationGroup


class RenderView(AbstractSceneObject):
    view_count = 0

    @classmethod
    def _next_name(cls):
        cls.view_count += 1
        return f"renderview_{cls.view_count}"

    def __init__(self, name=None):
        # Helper
        self.representations = RepresentationGroup(self)

        # VTK
        self.renderer = vtkRenderer(background=(0.8, 0.8, 0.8))
        self.interactor = vtkRenderWindowInteractor()
        self.render_window = vtkRenderWindow(off_screen_rendering=1)

        self.render_window.AddRenderer(self.renderer)
        self.interactor.SetRenderWindow(self.render_window)
        self.interactor.GetInteractorStyle().SetCurrentStyleToTrackballCamera()

        self.interactor.Initialize()

        axes_actor = vtkAxesActor()
        self.orientation_marker_widget = vtkOrientationMarkerWidget()
        self.orientation_marker_widget.SetOrientationMarker(axes_actor)
        self.orientation_marker_widget.SetInteractor(self.interactor)
        self.orientation_marker_widget.SetViewport(0.85, 0, 1, 0.15)
        self.orientation_marker_widget.EnabledOn()
        self.orientation_marker_widget.InteractiveOff()

        self.time_value = float("nan")
        # parent
        if name is None:
            name = self._next_name()
        super().__init__(group="views", name=name)

    def render(self, time_value=None):
        if time_value is not None:
            self.update(time_value)

        self.render_window.Render()

    def reset_camera(self):
        self.renderer.ResetCamera()

    def create_representation(self, source, name=None, type="Geometry"):
        rep_name = f"{type}Representation"
        rep_class = getattr(representations, rep_name)
        if rep_class is None:
            msg = f"Invalid representation name: {rep_name}"
            raise ValueError(msg)

        rep = rep_class(source, name=name)
        self.representations += rep
        return rep

    @property
    def time_values(self):
        all_values = set()
        for rep in self.representations.values():
            all_values = all_values.union(rep.time_values())
        return tuple(sorted(all_values))

    def update(self, time_value=None):
        if time_value is not None:
            self.time_value = time_value

        for rep in self.representations.values():
            rep.time_value = self.time_value
            rep.update()
