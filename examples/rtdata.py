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

import vtk
from trame.app import TrameApp
from trame.decorators import change
from trame.ui.vuetify3 import SinglePageLayout
from trame.widgets import vtk as vtkw
from trame.widgets import vuetify3 as v3

from vtk_scene import RenderView, SceneManager
from vtk_scene.lut import PRESETS
from vtk_scene.utils import get_range


class App(TrameApp):
    def __init__(self, server=None):
        super().__init__(server)

        # VTK
        self.rtdata_source = vtk.vtkRTAnalyticSource()
        self.view = RenderView()
        self.rep = self.view.create_representation(
            source=self.rtdata_source,
            type="Geometry",
        )
        self.rep.color_by("RTData")
        self.lut = SceneManager.active_scene.luts["RTData"]
        self.view.reset_camera()

        self.data_range = [
            float(v) for v in get_range(self.rep.input_data.point_data["RTData"])
        ]

        # GUI
        with SinglePageLayout(self.server, full_height=True) as self.ui:
            with self.ui.toolbar as toolbar:
                toolbar.density = "compact"
                v3.VSpacer()
                v3.VSelect(
                    v_model=("preset", "Fast"),
                    items=("preset_names", list(PRESETS.keys())),
                    density="compact",
                    hide_details=True,
                    classes="mx-2",
                    style="max-width: 200px;",
                )
                v3.VRangeSlider(
                    v_model=("color_range", self.data_range),
                    density="compact",
                    hide_details=True,
                    step=1,
                    min=self.data_range[0],
                    max=self.data_range[1],
                )
                v3.VBtn(
                    icon="mdi-crop-free",
                    click=self.ctrl.reset_camera,
                )

            with self.ui.content:
                vtkw.VtkRemoteView(
                    self.view.render_window,
                    interactive_ratio=1,
                    ctx_name="view",
                )
                self.ctrl.reset_camera = self.ctx.view.reset_camera

    @change("color_range")
    def on_color_range(self, color_range, **_):
        print(f"{color_range=}")
        self.lut.rescale(*color_range)
        self.ctx.view.update()

    @change("preset")
    def on_preset(self, preset, **_):
        print(f"{preset=}")
        self.lut.apply_preset(preset)
        self.ctx.view.update()


def main():
    app = App()
    app.server.start()


if __name__ == "__main__":
    main()
