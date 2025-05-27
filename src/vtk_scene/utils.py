import sys
from dataclasses import dataclass
from enum import Enum, auto

import numpy as np
from vtkmodules.numpy_interface.dataset_adapter import VTKCompositeDataArray
from vtkmodules.vtkCommonCore import vtkDataArray
from vtkmodules.vtkCommonDataModel import (
    vtkDataSet,
    vtkPartitionedDataSet,
    vtkPartitionedDataSetCollection,
)


@dataclass
class FieldInfo:
    location: str
    mapper_update: str
    description: str


@dataclass
class ColorInfo:
    name: str
    method: str
    vector_component: int


class ColorMode(Enum):
    RGB = ColorInfo("Direct color mapping", "SetVectorModeToRGBColors", -1)
    FieldMagnitude = ColorInfo("Magnitude", "SetVectorModeToMagnitude", -1)
    FieldComponent1 = ColorInfo("X", "SetVectorModeToComponent", 0)
    FieldComponent2 = ColorInfo("Y", "SetVectorModeToComponent", 1)
    FieldComponent3 = ColorInfo("Z", "SetVectorModeToComponent", 2)
    FieldComponent4 = ColorInfo("Component 4", "SetVectorModeToComponent", 3)
    FieldComponent5 = ColorInfo("Component 5", "SetVectorModeToComponent", 4)
    FieldComponent6 = ColorInfo("Component 6", "SetVectorModeToComponent", 5)
    FieldComponent7 = ColorInfo("Component 6", "SetVectorModeToComponent", 6)
    FieldComponent8 = ColorInfo("Component 6", "SetVectorModeToComponent", 7)
    FieldComponent9 = ColorInfo("Component 6", "SetVectorModeToComponent", 8)

    def __init__(self, info: ColorInfo):
        self._value_ = auto()
        self.lut_fn = info.method
        self.label = info.name
        self.vector_component = info.vector_component

    def apply(self, lut):
        getattr(lut, self.lut_fn)()
        lut.SetVectorComponent(self.vector_component)

    @staticmethod
    def components(size):
        if size > 1:
            return (
                ColorMode.FieldComponent1,
                ColorMode.FieldComponent2,
                ColorMode.FieldComponent3,
                ColorMode.FieldComponent4,
                ColorMode.FieldComponent5,
                ColorMode.FieldComponent6,
                ColorMode.FieldComponent7,
                ColorMode.FieldComponent8,
                ColorMode.FieldComponent9,
            )[:size]
        return ()

    @classmethod
    def options(cls, array):
        results = [
            cls.FieldMagnitude,
        ]

        # Just extract one of the composite array to figure out field shape
        if isinstance(array, VTKCompositeDataArray):
            for entry in array.Arrays:
                if entry is not None and entry.GetNumberOfTuples() > 0:
                    array = entry
                    break

        if isinstance(array, np.ndarray):
            number_of_components = array.shape[-1]
            dtype = array.dtype
            if dtype in (np.uint8, np.int8) and number_of_components in (3, 4):
                results.append(cls.RGB)
            results.extend(cls.components(array.number_of_components))

        elif hasattr(array, "IsA") and array.IsA("vtkDataArray"):
            if array.number_of_components == 3 or (
                array.number_of_components == 4 and array.GetDataTypeSize() == 1
            ):
                results.append(cls.RGB)

            results.extend(cls.components(array.number_of_components))

        return results


class FieldLocation(Enum):
    PointData = FieldInfo(
        "point_data", "SetScalarModeToUsePointFieldData", "Data located on points"
    )
    CellData = FieldInfo(
        "cell_data", "SetScalarModeToUseCellFieldData", "Data located on cells"
    )
    FieldData = FieldInfo(
        "field_data", "SetScalarModeToUseFieldData", "Data located on dataset"
    )
    UnAvailable = FieldInfo("", "", "No field coloring")

    def __init__(self, info: FieldInfo):
        self._value_ = info.location
        self.mapper_fn = info.mapper_update
        self.comment = info.description

    def select(self, mapper):
        if self.mapper_fn:
            mapper.SetScalarVisibility(1)
            getattr(mapper, self.mapper_fn)()
        else:
            mapper.SetScalarVisibility(0)

    @classmethod
    def get(cls, value):
        for option in cls:
            if option.value == value:
                return option

        return cls.UnAvailable

    @classmethod
    def find(cls, dataset, field_name, lookup_order=None):
        if dataset is None:
            return cls.UnAvailable

        if lookup_order is None:
            lookup_order = [cls.PointData, cls.CellData, cls.FieldData]

        for location in lookup_order:
            available_fields = getattr(dataset, location.value).keys()
            if field_name in available_fields:
                return location

        return cls.UnAvailable

    def get_array(self, ds, field_name):
        if self.value:
            return getattr(ds, self.value)[field_name]
        return None

    def field_names(self, ds):
        if self.value:
            return list(getattr(ds, self.value).keys())
        return []


# -----------------------------------------------------------------------------
# Internal Helpers
# -----------------------------------------------------------------------------


def merge_range(a, b):
    if a is None:
        return b
    if b is None:
        return a
    return (min(a[0], b[0]), max(a[1], b[1]))


def merge_bounds(a, b):
    if a is None:
        return b
    if b is None:
        return a
    return (
        min(a[0], b[0]),
        max(a[1], b[1]),
        min(a[2], b[2]),
        max(a[3], b[3]),
        min(a[4], b[4]),
        max(a[5], b[5]),
    )


# -----------------------------------------------------------------------------
# Helper for composite structures
# -----------------------------------------------------------------------------

EMPTY_BOUNDS = (
    -sys.float_info.max,
    sys.float_info.max,
    -sys.float_info.max,
    sys.float_info.max,
    -sys.float_info.max,
    sys.float_info.max,
)


def get_bounds(ds):
    if ds is None:
        return EMPTY_BOUNDS

    if isinstance(ds, vtkDataSet):
        return ds.bounds
    if isinstance(ds, vtkPartitionedDataSet):
        size = ds.GetNumberOfPartitions()
        bounds = None
        for i in range(size):
            pds = ds.GetPartition(i)
            bounds = merge_bounds(bounds, get_bounds(pds))
        return bounds
    if isinstance(ds, vtkPartitionedDataSetCollection):
        size = ds.GetNumberOfPartitionedDataSets()
        bounds = None
        for i in range(size):
            pds = ds.GetPartitionedDataSet(i)
            bounds = merge_bounds(bounds, get_bounds(pds))
        return bounds
    return EMPTY_BOUNDS


# -----------------------------------------------------------------------------


def get_range(array, component=-1):
    """VTK array range helper"""
    if isinstance(array, vtkDataArray):
        return array.GetRange(component)
    if isinstance(array, VTKCompositeDataArray):
        full_range = None
        for entry in array.Arrays:
            full_range = merge_range(full_range, entry.GetRange(component))
        return full_range
    if isinstance(array, np.ndarray):
        shape = array.shape
        if len(shape) == 1:
            min_value = array.min()
            max_value = array.max()
            return (min_value, max_value)
        if component >= 0:
            component_array = array[component]
            min_value = component_array.min()
            max_value = component_array.max()
            return (min_value, max_value)
        msg = "Don't know how to compute np.array magnitude"
        raise ValueError(msg)

    msg = f"Don't know what to do with {type(array)}"
    raise ValueError(msg)
