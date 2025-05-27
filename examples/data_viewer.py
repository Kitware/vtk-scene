"""
Code example covering:
- reading file
- showing it in a view
- listing available arrays
- coloring by an available array
- changing color preset
- adjusting color range
- adjusting time
"""

from trame.app import TrameApp
from trame.decorators import change
from trame.ui.vuetify3 import SinglePageLayout
from trame.widgets import rca
from trame.widgets import vuetify3 as v3

from vtk_scene import ColorMode, FieldLocation, RenderView, SceneManager
from vtk_scene.io import ReaderFactory
from vtk_scene.lut import PRESETS
from vtk_scene.utils import get_range

LOCATION_FIELD_SEPARATOR = "||"

COLOR_MODE_MAPPING = {mode.label: mode for mode in ColorMode}


def map_to_items(fields):
    result = []
    for location, field_names in fields.items():
        for name in field_names:
            result.append(
                {
                    "title": name,
                    "value": f"{location.value}{LOCATION_FIELD_SEPARATOR}{name}",
                }
            )
    return result


class App(TrameApp):
    def __init__(self, server=None):
        super().__init__(server)

        cli = self.server.cli
        cli.add_argument("--data", help="Path to file to load", required=True)
        args, _ = cli.parse_known_args()

        # VTK
        self.reader = ReaderFactory.create(args.data)
        self.view = RenderView()
        self.representation = self.view.create_representation(
            source=self.reader,
            name="reader",
            type="Geometry",
        )
        self.view.reset_camera()

        # GUI
        self.state.color_modes = []
        self.state.fields = map_to_items(self.representation.available_fields)
        self.state.time_values = self.view.time_values
        self.state.map_scalar = True
        with SinglePageLayout(self.server, full_height=True) as self.ui:
            with self.ui.toolbar as toolbar:
                toolbar.density = "compact"
                v3.VSpacer()
                v3.VLabel(
                    "t={{ time_values[t_index] }} ({{ t_index + 1 }}/{{ time_values.length }})",
                    classes="mr-2 text-caption",
                )
                v3.VSelect(
                    v_model=("color_mode", None),
                    items=("color_modes", []),
                    density="compact",
                    hide_details=True,
                    style="max-width: 200px",
                    classes="ml-2",
                )
                v3.VSelect(
                    v_model=("color_by", ""),
                    items=("fields", []),
                    density="compact",
                    hide_details=True,
                    style="max-width: 200px",
                    classes="ml-2",
                )
                v3.VSelect(
                    v_model=("preset", "Fast"),
                    items=("presets", list(PRESETS.keys())),
                    density="compact",
                    hide_details=True,
                    style="max-width: 200px",
                    classes="ml-2",
                )
                v3.VBtn(
                    icon="mdi-arrow-expand-horizontal",
                    click=self.reset_color_range,
                )
                v3.VBtn(
                    icon="mdi-crop-free",
                    click=self.reset_camera,
                )

            with self.ui.content:
                with v3.VContainer(fluid=True, classes="h-100 ma-0 pa-0"):
                    with rca.RemoteControlledArea(
                        name="removeView",
                        display="image",
                    ) as view:
                        handler = view.create_view_handler(self.view.render_window)
                        self.ctrl.view_update = handler.update

            with self.ui.footer.clear() as footer:
                footer.classes = "pl-0 py-0"
                footer.v_show = "time_values.length > 1"
                v3.VSlider(
                    v_model=("t_index", 0),
                    min=0,
                    max=("time_values.length - 1",),
                    step=1,
                    hide_details=True,
                    density="compact",
                    prepend_icon="mdi-clock-time-eight-outline",
                )

    def reset_camera(self):
        self.view.reset_camera()
        self.ctrl.view_update()

    def reset_color_range(self):
        mode = COLOR_MODE_MAPPING[self.state.color_mode]
        location, field_name = self.state.color_by.split(LOCATION_FIELD_SEPARATOR)
        field_location = FieldLocation.get(location)
        array = field_location.get_array(self.representation.input_data, field_name)
        min_value, max_value = get_range(array, mode.vector_component)
        lut = SceneManager.active_scene.luts[field_name]
        lut.rescale(min_value, max_value)
        self.ctrl.view_update()

    @change("color_by")
    def on_color_by(self, color_by, **_):
        if not color_by:
            self.representation.color_by(None)
        else:
            location, field_name = color_by.split(LOCATION_FIELD_SEPARATOR)
            field_location = FieldLocation.get(location)
            self.representation.color_by(field_name, field_location, reset_range=True)
            array = field_location.get_array(self.representation.input_data, field_name)
            if array is not None:
                self.state.color_modes = [v.label for v in ColorMode.options(array)]
                self.state.color_mode = self.state.color_modes[0]
            else:
                self.state.color_modes = []
                self.state.color_mode = None

        self.ctrl.view_update()

    @change("color_mode")
    def on_color_mode(self, color_mode, color_by, **_):
        if color_mode is None or not color_by:
            return

        _, field_name = color_by.split(LOCATION_FIELD_SEPARATOR)
        lut = SceneManager.active_scene.luts[field_name]
        if lut:
            lut.color_mode = COLOR_MODE_MAPPING[color_mode]
            self.reset_color_range()

    @change("preset")
    def on_preset(self, preset, color_by, **_):
        if not color_by:
            return
        _, field_name = color_by.split(LOCATION_FIELD_SEPARATOR)
        lut = SceneManager.active_scene.luts[field_name]
        if lut:
            lut.apply_preset(preset)
            self.ctrl.view_update()

    @change("t_index")
    def on_time_change(self, t_index, time_values, **_):
        if len(time_values):
            self.view.update(time_values[t_index])
        self.ctrl.view_update()


def main():
    app = App()
    app.server.start()


if __name__ == "__main__":
    main()
