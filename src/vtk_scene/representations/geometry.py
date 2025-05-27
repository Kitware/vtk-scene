import logging

from vtkmodules.vtkCommonExecutionModel import (
    vtkStreamingDemandDrivenPipeline as vtkSDDP,
)
from vtkmodules.vtkFiltersGeometry import vtkDataSetSurfaceFilter
from vtkmodules.vtkRenderingCore import (
    vtkActor,
    vtkCompositePolyDataMapper,
)

from vtk_scene.lut import LookupTable
from vtk_scene.representations.core import AbstractRepresentation
from vtk_scene.utils import FieldLocation, get_range

logger = logging.getLogger(__name__)

# logging.basicConfig(level=logging.CRITICAL)
# logger.setLevel(logging.DEBUG)


class GeometryRepresentation(AbstractRepresentation):
    def __init__(self, input, name=None, **_):
        super().__init__(name)

        # internal
        self._input = input

        self.time_value = float("nan")
        self.input_mtime = 0

        # VTK
        self.geometry = vtkDataSetSurfaceFilter()
        self.mapper = vtkCompositePolyDataMapper(
            input_connection=self.geometry.output_port,
        )
        # self.mapper = vtkPolyDataMapper(
        #     input_connection=self.geometry.output_port,
        # )
        self.actor = vtkActor(mapper=self.mapper)

        if self._input.IsA("vtkDataObject"):
            self.geometry.input_data = self._input

        self.update()

    def add_view(self, view):
        if view not in self._views:
            self._views.append(view)
            view.renderer.AddActor(self.actor)

    def remove_view(self, view):
        if view in self._views:
            self._views.remove(view)
            view.renderer.RemoveActor(self.actor)

    @property
    def input(self):
        return self._input

    @input.setter
    def input(self, new_input):
        if self._input != new_input:
            self._input = new_input
            if self._input.IsA("vtkDataObject"):
                self.geometry.input_data = self._input

    def time_values(self):
        if self._input.IsA("vtkAlgorithm"):
            self._input.UpdateInformation()
            oi = self._input.GetOutputInformation(0)
            if oi.Has(vtkSDDP.TIME_STEPS()):
                return oi.Get(vtkSDDP.TIME_STEPS())
        return ()

    def update(self):
        if self._input.IsA("vtkAlgorithm"):
            import math

            if math.isnan(self.time_value):
                self._input.Update()
            else:
                self._input.UpdateTimeStep(self.time_value)
            mtime = self._input.GetOutputDataObject(0).GetMTime()
            if mtime > self.input_mtime:
                self.input_mtime = mtime
                dobj = self._input.GetOutputDataObject(0)
                dobj_c = dobj.NewInstance()
                dobj_c.ShallowCopy(dobj)
                self.geometry.input_data = dobj_c

            return self._input.GetOutputDataObject(0)

        return self._input

    @property
    def input_data(self):
        return self.geometry.input

    @property
    def available_fields(self):
        dataset = self.update()
        return {
            FieldLocation.PointData: FieldLocation.PointData.field_names(dataset),
            FieldLocation.CellData: FieldLocation.CellData.field_names(dataset),
            FieldLocation.FieldData: FieldLocation.FieldData.field_names(dataset),
        }

    def color_by(
        self,
        field_name,
        field_location: FieldLocation = None,
        preset=None,
        reset_range=False,
        map_scalar=True,
    ):
        logger.debug(
            "color_by: field_name=%s, field_location=%s, preset=%s, reset_range=%s, map_scalar=%s",
            field_name,
            field_location,
            preset,
            reset_range,
            map_scalar,
        )
        if not field_name:
            self.mapper.SetScalarVisibility(0)
            return

        self.mapper.SetScalarVisibility(1)
        lut = self.scene.luts[field_name]
        if lut is None:
            lut = LookupTable(field_name)
            reset_range = True

        if preset:
            lut.apply_preset(preset)

        if reset_range:
            logger.debug("color_by: reset_range")
            self.update()
            dataset = self.input_data
            if field_location is None:
                field_location = FieldLocation.find(dataset, field_name)
            array = field_location.get_array(dataset, field_name)

            if array is not None:
                logger.debug("color_by => rescale %s=%s", field_name, get_range(array))
                lut.rescale(*get_range(array))

        if map_scalar:
            logger.debug("color_by => SetColorModeToMapScalars")
            self.mapper.SetColorModeToMapScalars()
        else:
            logger.debug("color_by => SetColorModeToDirectScalars")
            self.mapper.SetColorModeToDirectScalars()

        self.mapper.SelectColorArray(field_name)
        self.mapper.SetLookupTable(lut)

        if field_location is None:
            self.update()
            dataset = self.input_data
            field_location = FieldLocation.find(dataset, field_name)

        if field_location is None:
            field_location = FieldLocation.PointData

        logger.debug("color_by => %s", field_location)
        field_location.select(self.mapper)
