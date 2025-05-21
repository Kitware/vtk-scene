# /// script
# requires-python = ">=3.9"
# dependencies = [
#     "trame>=3.9",
#     "trame-vtk",
#     "trame-vuetify",
#     "vtk-scene",
# ]
#
# [tool.uv.sources]
# vtk-scene = { path = "../" }
# ///
import random

from trame.app import TrameApp
from trame.decorators import change
from trame.ui.vuetify3 import SinglePageLayout
from trame.widgets import vtk as vtkw
from trame.widgets import vuetify3 as v3
from vtkmodules.vtkFiltersSources import vtkConeSource

from vtk_scene import RenderView


class App(TrameApp):
    def __init__(self, server=None):
        super().__init__(server)

        # VTK
        self.cone = vtkConeSource()
        self.view = RenderView()
        self.rep = self.view.create_representation(
            name="cone",
            source=self.cone,
            type="Geometry",
        )
        self.view.reset_camera()

        # GUI
        with SinglePageLayout(self.server, full_height=True) as self.ui:
            with self.ui.toolbar as toolbar:
                toolbar.density = "compact"
                v3.VSpacer()
                v3.VSlider(
                    v_model=("resolution", 6),
                    density="compact",
                    hide_details=True,
                    step=1,
                    min=3,
                    max=60,
                )
                v3.VBtn(
                    icon="mdi-crop-free",
                    click=self.ctrl.reset_camera,
                )
                v3.VCheckbox(
                    true_icon="mdi-eye-outline",
                    false_icon="mdi-eye-off-outline",
                    v_model=("show_cone", True),
                    density="compact",
                    hide_details=True,
                    classes="mr-4",
                )

            with self.ui.content:
                with v3.VContainer(fluid=True, classes="h-100 ma-0 pa-0"):
                    vtkw.VtkRemoteView(
                        self.view.render_window, interactive_ratio=1, ctx_name="view"
                    )
                    self.ctrl.reset_camera = self.ctx.view.reset_camera

    @change("resolution")
    def on_resolution(self, resolution, **_):
        # update cone source with new resolution
        self.cone.resolution = resolution

        # if rep exist grab and edit it
        if "cone" in self.view.representations:
            rep = self.view.representations["cone"]
            rep.actor.property.color = (
                random.random(),
                random.random(),
                random.random(),
            )

            # flush pipeline for new resolution
            rep.update()

        # make the web ui update its view
        self.ctx.view.update()

    @change("show_cone")
    def on_show(self, show_cone, **_):
        if show_cone:
            # add representation
            self.view.representations += self.rep

            # flush pipeline in case of different resolution
            self.rep.update()

            # reset camera on server side
            self.view.reset_camera()
        else:
            # remove representation (hide)
            self.view.representations -= self.rep

        # make the web ui update its view
        self.ctx.view.update()


def main():
    app = App()
    app.server.start()


if __name__ == "__main__":
    main()
