#!/usr/bin/env -S uv run --script
#
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "pan3d[all]",
#     "vtk==9.5.0rc2",
#     "trame>=3.10",
#     "trame-rca",
#     "vtk-scene",
# ]
#
# [[tool.uv.index]]
# url = "https://wheels.vtk.org"
#
# [tool.uv.sources]
# vtk-scene = { url = "https://github.com/Kitware/vtk-scene/releases/download/v0.1.3/vtk_scene-0.1.3-py3-none-any.whl" }
# ///
import asyncio

import xarray as xr
from pan3d.xarray.algorithm import vtkXArrayRectilinearSource
from trame.app import TrameApp, asynchronous
from trame.decorators import change
from trame.ui.vuetify3 import VAppLayout
from trame.widgets import rca
from trame.widgets import vuetify3 as v3
from vtkmodules.vtkCommonDataModel import vtkDataObject, vtkPlane
from vtkmodules.vtkFiltersCore import vtkCutter

from vtk_scene import RenderView, SceneManager
from vtk_scene.utils import get_bounds, get_range

USE_CLIP = False


class PFlotranViewer(TrameApp):
    def __init__(self, server=None):
        super().__init__(server)

        # CLI
        self.server.cli.add_argument(
            "--url",
            type=str,
            default="https://storage.googleapis.com/pan3d-public-01/pfsmall/pfsmall-gcp.json",
            help="URL for reference filesystem definition",
        )
        self.ref_fs_url = self.server.cli.parse_known_args()[0].url

        self._setup_vtk()
        self._build_ui()

    def _setup_vtk(self):
        # Read dataset
        xr_dataset = xr.open_dataset(
            "reference://",
            engine="zarr",
            mask_and_scale=False,
            backend_kwargs={
                "consolidated": False,
                "storage_options": {"fo": self.ref_fs_url},
            },
        )
        self.reader = vtkXArrayRectilinearSource(xr_dataset)
        ds = self.reader()

        # Create VTK objects
        self.bounds = get_bounds(ds)
        self.plane = vtkPlane()
        self.plane.origin = [
            0.5 * (self.bounds[0] + self.bounds[1]),
            0.5 * (self.bounds[2] + self.bounds[3]),
            0.5 * (self.bounds[4] + self.bounds[5]),
        ]
        self.slice = vtkCutter(cut_function=self.plane)

        # Fill drop down with available fields
        self.state.available_fields = list(ds.point_data)
        self.state.time_index_max = self.reader.t_size - 1

        # Remove empty material
        filter = None
        if USE_CLIP:
            from vtkmodules.vtkFiltersGeneral import vtkClipDataSet

            filter = vtkClipDataSet(value=1, use_value_as_offset=0)
        else:
            from vtkmodules.vtkFiltersCore import vtkThreshold

            filter = vtkThreshold(
                threshold_function=vtkThreshold.THRESHOLD_UPPER,
                upper_threshold=0.1,
            )
        filter.SetInputArrayToProcess(
            0,
            0,
            0,
            vtkDataObject.FIELD_ASSOCIATION_POINTS,
            "Material_ID",
        )

        # Connect pipeline
        self.reader >> filter >> self.slice

        # vtk scene
        self.view = RenderView()
        self.rep_reader = self.view.create_representation(filter, name="reader")
        self.rep_cut = self.view.create_representation(self.slice, name="cut")
        self.view.reset_camera()

    def _build_ui(self):
        with VAppLayout(self.server, full_height=True) as self.ui:
            with v3.VFooter(
                app=True, classes="d-flex align-center pl-0 py-1 bg-grey-lighten-4"
            ):
                v3.VSlider(
                    prepend_icon="mdi-clock-time-eight-outline",
                    v_model=("time_index", 0),
                    min=0,
                    max=("time_index_max", 0),
                    step=1,
                    hide_details=True,
                    density="compact",
                    style="min-width: 100px",
                )

                v3.VBtn(
                    icon="mdi-skip-previous",
                    disabled=("time_index === 0",),
                    click="time_index--",
                    hide_details=True,
                    density="compact",
                    flat=True,
                    tile=True,
                    classes="ml-2",
                )
                v3.VBtn(
                    v_if=("playing", False),
                    icon="mdi-stop",
                    click="playing=false",
                    hide_details=True,
                    density="compact",
                    flat=True,
                    tile=True,
                )
                v3.VBtn(
                    v_else=True,
                    icon="mdi-play",
                    click="playing=true",
                    hide_details=True,
                    density="compact",
                    flat=True,
                    tile=True,
                )
                v3.VBtn(
                    icon="mdi-skip-next",
                    disabled=("time_index === time_index_max",),
                    click="time_index++",
                    hide_details=True,
                    density="compact",
                    flat=True,
                    tile=True,
                )
                v3.VDivider(vertical=True, classes="ml-2")
                v3.VSlider(
                    disabled=("slice_axis == null",),
                    prepend_icon="mdi-box-cutter",
                    v_model=("slice_location", 0.5),
                    min=0,
                    max=1,
                    step=0.01,
                    hide_details=True,
                    density="compact",
                )
                with v3.VBtnToggle(
                    v_model=("slice_axis", None),
                    divided=True,
                    border=True,
                    density="compact",
                    classes="ml-2",
                ):
                    v3.VBtn("X", size="x-small")
                    v3.VBtn("Y", size="x-small")
                    v3.VBtn("Z", size="x-small")

            with v3.VMain():
                with v3.VRow(
                    style="position:absolute;top:1rem;left:1rem;z-index:1;",
                    classes="align-center pa-0 ma-0",
                ):
                    v3.VSelect(
                        v_model=("color_by", ""),
                        items=("available_fields",),
                        style="width: 20rem",
                        hide_details=True,
                        density="compact",
                        variant="outlined",
                    )
                    v3.VBtn(
                        icon="mdi-arrow-collapse-horizontal",
                        click=self.reset_color_range,
                        hide_details=True,
                        density="compact",
                        flat=True,
                        variant="outlined",
                        classes="mx-4",
                    )
                with rca.RemoteControlledArea(
                    name="view",
                    display="image",
                ) as rca_view:
                    handler = rca_view.create_view_handler(self.view.render_window)
                    self.ctx.view = handler

    @change("color_by")
    def _on_color_by(self, color_by, **_):
        self.rep_reader.color_by(color_by)
        self.rep_cut.color_by(color_by)
        self.ctx.view.update()

    @change("slice_axis")
    def on_slice(self, slice_axis, color_by, **_):
        if slice_axis is None:
            self.rep_reader.actor.property.opacity = 1
            self.rep_reader.color_by(color_by)
            self.rep_reader.update()

            self.rep_cut.actor.visibility = 0
            self.rep_cut.update()
        else:
            self.rep_reader.actor.property.opacity = 0.2
            self.rep_reader.color_by(None)
            self.rep_reader.update()

            # Update slice normal
            normal = [0, 0, 0]
            normal[slice_axis] = 1
            self.plane.normal = normal

            self.rep_cut.actor.visibility = 1
            self.rep_cut.color_by(color_by)
            self.rep_cut.update()

        # Render all views
        self.ctx.view.update()

    @change("slice_location")
    def on_slice_location(self, slice_location, slice_axis, **_):
        origin = [
            slice_location * (self.bounds[1] - self.bounds[0]) + self.bounds[0],
            slice_location * (self.bounds[3] - self.bounds[2]) + self.bounds[2],
            slice_location * (self.bounds[5] - self.bounds[4]) + self.bounds[4],
        ]
        self.plane.origin = origin
        self.rep_cut.update()

        if slice_axis is not None:
            self.ctx.view.update()

    @change("time_index")
    def on_time(self, time_index, **_):
        self.reader.t_index = time_index
        self.rep_reader.update()
        self.rep_cut.update()
        self.ctx.view.update()

    @change("playing")
    def on_playing(self, playing, **_):
        if playing:
            asynchronous.create_task(self._next_timestep())

    def reset_color_range(self):
        color_by = self.state.color_by
        lut = SceneManager.active_scene.luts[color_by]
        ds = None
        if self.state.slice_axis is None:
            ds = self.reader()
        else:
            self.slice.Update()
            ds = self.slice.GetOutput()
        data_range = get_range(ds.point_data[color_by])
        lut.rescale(*data_range)
        self.ctx.view.update()

    async def _next_timestep(self):
        with self.state as state:
            if state.playing:
                if state.time_index < state.time_index_max:
                    state.time_index += 1
                else:
                    state.playing = False

        await asyncio.sleep(0.5)
        if self.state.playing:
            asynchronous.create_task(self._next_timestep())


def main():
    app = PFlotranViewer()
    app.server.start()


if __name__ == "__main__":
    main()
