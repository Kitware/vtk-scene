import json
from pathlib import Path

from vtkmodules.vtkRenderingCore import vtkColorTransferFunction

from vtk_scene.core import AbstractSceneObject
from vtk_scene.utils import ColorMode

PRESETS = {
    item.get("Name"): item
    for item in json.loads(Path(__file__).with_name("presets.json").read_text())
}


class LookupTable(vtkColorTransferFunction, AbstractSceneObject):
    def __init__(
        self, field_name, preset_name="Fast", color_mode=ColorMode.FieldMagnitude
    ):
        AbstractSceneObject.__init__(self, "luts", field_name)
        self._color_mode = color_mode or ColorMode.FieldMagnitude
        self._scalar_range = [0, 1]
        self.apply_preset(preset_name)

        # Apply settings
        self._color_mode.apply(self)

    def apply_preset(self, preset_name):
        preset = PRESETS.get(preset_name)
        if preset is None:
            msg = f"Invalid preset name: {preset_name}"
            raise ValueError(msg)

        srgb = preset["RGBPoints"]
        color_space = preset["ColorSpace"]

        if color_space == "Diverging":
            self.SetColorSpaceToDiverging()
        elif color_space == "HSV":
            self.SetColorSpaceToHSV()
        elif color_space == "Lab":
            self.SetColorSpaceToLab()
        elif color_space == "RGB":
            self.SetColorSpaceToRGB()
        elif color_space == "CIELAB":
            self.SetColorSpaceToLabCIEDE2000()

        if "NanColor" in preset:
            self.SetNanColor(preset["NanColor"])

        # Always RGB points
        self.RemoveAllPoints()
        for i in range(0, len(srgb), 4):
            self.AddRGBPoint(srgb[i], srgb[i + 1], srgb[i + 2], srgb[i + 3])

        # Rescale to current data range
        self.rescale(*self._scalar_range)

    def rescale(self, min_value, max_value):
        prev_min, prev_max = self.GetRange()

        prev_delta = prev_max - prev_min
        next_delta = max_value - min_value

        if prev_delta < 0.0000001 or next_delta < 0.0000001:
            return

        self._scalar_range = [min_value, max_value]
        node = [0, 0, 0, 0, 0, 0]
        next_nodes = []
        for i in range(self.GetSize()):
            self.GetNodeValue(i, node)
            node[0] = next_delta * (node[0] - prev_min) / prev_delta + min_value
            next_nodes.append(list(node))

        self.RemoveAllPoints()
        for n in next_nodes:
            self.AddRGBPoint(*n)

    @property
    def color_mode(self):
        return self._color_mode

    @color_mode.setter
    def color_mode(self, v: ColorMode):
        self._color_mode = v
        self._color_mode.apply(self)
