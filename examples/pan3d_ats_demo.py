import asyncio

from trame.app import TrameApp, asynchronous
from trame.decorators import change
from trame.ui.vuetify3 import VAppLayout
from trame.widgets import rca
from trame.widgets import vuetify3 as v3
from vtkmodules.vtkCommonDataModel import vtkDataObject
from vtkmodules.vtkFiltersCore import vtkThreshold

from vtk_scene import FieldLocation, RenderView, SceneManager
from vtk_scene.io import ReaderFactory

COLS = {
    1: 12,
    2: 6,
    3: 4,
    4: 6,
    5: 4,
    6: 4,
    7: 3,
    8: 3,
    9: 4,
    10: 4,
    11: 4,
    12: 4,
}


class MultiView(TrameApp):
    def __init__(self, server=None):
        super().__init__(server)

        # Add cli
        cli = self.server.cli
        cli.add_argument("--data", help="Path to pre-process data file")
        cli.add_argument("--fields", help="Fields to display", nargs="+")
        args, _ = cli.parse_known_args()

        self.fields = args.fields
        self._setup_vtk(args.data, args.fields)
        self._build_ui(COLS[len(args.fields)])

    def _setup_vtk(self, file_to_load, fields):
        self.views = {}
        self.representations = {"reader": [], "pounding": []}
        self.reader = ReaderFactory.create(file_to_load)
        self.threshold = vtkThreshold(
            threshold_function=vtkThreshold.THRESHOLD_UPPER,
            upper_threshold=0,
        )
        self.threshold.SetInputArrayToProcess(
            0, 0, 0, vtkDataObject.FIELD_ASSOCIATION_CELLS, "surface-ponded_depth"
        )
        self.reader >> self.threshold

        # Time info for UI
        self.state.time_values = self.reader.time_values
        self.state.time_index_max = len(self.state.time_values) - 1

        print("-" * 60)
        print("Available fields:")
        for name in self.reader().cell_data.keys():
            print(f" - {name}")
        print("-" * 60)

        for name in fields:
            # Create viz
            view = RenderView()
            rep = view.create_representation(self.reader, name=name, type="Geometry")
            rep.color_by(name)
            self.representations["reader"].append(rep)

            rep = view.create_representation(
                self.threshold, name=f"pounding_{name}", type="Geometry"
            )
            rep.actor.position = (0, 0, 1)
            self.representations["pounding"].append(rep)
            view.reset_camera()

            # Sync camera
            camera = view.renderer.active_camera
            camera.AddObserver("ModifiedEvent", self._on_camera_change)

            # Keep track of the view
            self.views[name] = view

    def rescale(self, grow=False):
        print("rescale grow", grow)
        for rep, name in zip(self.representations["reader"], self.views.keys()):
            lut = SceneManager.active_scene.luts[name]
            dataset = rep.mapper.GetInput()
            array = FieldLocation.CellData.get_array(dataset, name)

            if array is not None:
                if grow:
                    old_min, old_max = lut.scalar_range
                    current_min, current_max = array.GetRange()
                    lut.rescale(min(old_min, current_min), max(old_max, current_max))
                else:
                    lut.rescale(*array.GetRange())

        self.ctrl.view_update_all()

    def _on_camera_change(self, camera, *_):
        for field, view in self.views.items():
            if view.renderer.active_camera == camera:
                continue
            view.renderer.active_camera.ShallowCopy(camera)
            self.ctrl[f"view_update_{field}"]()

    def _build_ui(self, n_cols):
        with VAppLayout(self.server, full_height=True) as self.ui:
            with v3.VLayout(full_height=True):
                with v3.VMain():
                    with v3.VContainer(classes="h-100 pa-0 ma-0", fluid=True):
                        with v3.VRow(no_gutters=True, classes="h-100"):
                            for field_name, view in self.views.items():
                                with v3.VCol(cols=n_cols):
                                    v3.VLabel(
                                        field_name,
                                        classes="position-absolute text-subtitle-1 pa-2",
                                        style="z-index: 1;",
                                    )
                                    with rca.RemoteControlledArea(
                                        name=field_name,
                                        display="image",
                                        classes="border-thin",
                                    ) as rca_view:
                                        handler = rca_view.create_view_handler(
                                            view.render_window
                                        )
                                        self.ctrl[f"view_update_{field_name}"] = (
                                            handler.update
                                        )
                                        self.ctrl.view_update_all.add(handler.update)

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
                        click_prepend=(self.rescale, "[$event.altKey]"),
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
                        prepend_icon="mdi-waves-arrow-up",
                        v_model=("pounding", 0.5),
                        min=0.01,
                        max=1,
                        step=0.01,
                        hide_details=True,
                        density="compact",
                    )

    @change("pounding")
    def on_pounding(self, pounding, **_):
        self.threshold.upper_threshold = pounding
        for rep in self.representations["pounding"]:
            rep.update()

        # Render all views
        self.ctrl.view_update_all()

    @change("time_index")
    def on_time(self, time_index, time_values, **_):
        for view in self.views.values():
            view.update(time_values[time_index])
        self.ctrl.view_update_all()

    @change("playing")
    def on_playing(self, playing, **_):
        if playing:
            asynchronous.create_task(self._next_timestep())

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
    app = MultiView()
    app.server.start()


if __name__ == "__main__":
    main()
