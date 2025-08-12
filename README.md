# vtk-scene

This is an **exploratory** project and is not aimed to be used in production.
Its intent is for us to explore how to make it easier to create VTK
visualization in Python leveraging the same concepts introduced within ParaView.
The API is expected to change at any time to support our exploration goals.
Please use it at your own risk.

- **What it is:** A Python library to use on top of VTK for creating interactive
  visualization mainly focusing on the rendering definition of a view taking cue
  from ParaView model.
- **Mission:** To provide a library that reduce the burden of defining VTK
  visualization pipelines.
- **Vision:** To create an open solution that is easy to maintain and expand
  while not limiting the user in any specific way.

## License

**vtk-scene** is made available under the Apache License, Version 2.0. For more
details, see [LICENSE](./LICENSE)

## Caution

This project is aimed to be used with VTK 9.5.

```
pip install "vtk>=9.5.0" --extra-index-url https://wheels.vtk.org
```

## Introduction

This library provide the following set of classes:

- `vtk_scene.SceneManager`: The scene manager is capturing views,
  representations, lookup tables and possible more depending on your usage. But
  the goal here is to have a central location where you can find your scene
  definition while also ensuring shared lookup table for fields with the same
  name.
- `vtk_scene.RenderView`: The render view is a wrapper around a vtkRenderWindow
  with some helper methods for configuring the interaction style and manage
  representations that belong to the view.
- `vtk_scene.FieldLocation`: Utility enum for defining data location (point,
  cell, field)
- `vtk_scene.ColorMode`: Utility enum (RGB, FieldMagnitude, FieldComponent1-9)
  for configuring the coloring mode on the Lookup table.

On top of those core objects you can create/get representations and lookup table
interacting with those classes like shown below

```python
import vtk
from vtk_scene import ColorMode, FieldLocation, RenderView, SceneManager

data_source = vtk.vtkRTAnalyticSource()
vtk_view = RenderView()

data_rep = vtk_view.create_representation(
    source=data_source,
    type="Geometry",
)
data_rep.color_by("RTData", preset="Cool to Warm")

lut = SceneManager.active_scene.luts["RTData"]
lut.rescale(40, 200)

vtk_view.reset_camera()
vtk_view.update()

print(f"Available time values: {vtk_view.time_values}")
```

## Capabilities per classes

### Views

The vtk-scene views are meant to simplify VTK visualization by creating all the
default pieces needed for any 3D visualization. This include orientation widget
along with convenient API for handling camera, time, data representation and
overlay annotation.

We currently have the `RenderView` which implements the following API

- **render(time_value=None)** to trigger an image computation using the
  time_value if provided.
- **reset_camera()** to compute the bounds of the scene and ensure that all the
  content fits into the view.
- **create_representation(source, name=None, type="Geometry") -> rep** to create
  a representation of the given type for the provided source. The source can
  either be a vtkAlgorithm or a vtkDataObject. The representation gets added to
  the view automatically.
- **time_values() -> tuple(float)** query the pipeline and return the set of
  times available across the sources visible in the view.
- **update(time_value=None)** update all the view's representation with the
  provided time.

Down the road we aim to provide control for defining the interactor style, and
overlay annotations with an API that could look like this.

- `add_manipulator(name, binding, action)` where binding could be
  `{ button_left: 1, modifiers: ('ctrl|alt|shift', 'alt&shift')` and action one
  of `trackball_rotate`, `pan`, `terrain_rotate`...
- `remove_manipulator(name)`
- `clear_manipulators()`
- `use_manipulator_preset(name)` with preset name like `3d`, `2d`, `fly`

And for annotation something like

- `clear_scalarbars()`
- `add_scalarbar(field_name)`
- `remove_scalarbar(field_name)`
- `layout_scalarbars(location="right", order=[field_names...], orientation="vertical")`

### Representation

Representations aim to simplify the visual representation of a data source with
simple and easy to use API. On a representation you can query the data to figure
out which fields are available to color your data with and also you are in
control on when you want to update the data.

The current user facing API is as follow

- `available_fields() -> Dict(location, list(names))`
- `color_by(field_name, field_location=None, preset=None, reset_range=False, map_scalar=True)`
- `update()` to force upstream filter execution.
- `time_values() -> tuple(float)`
- `input` (set/get property) for binding vtkDataObject or vtkAlgorithm.

### ColorMaps

The vtk-scene library provides a convenient API on top of a vtkLookupTable for
dealing with color mapping.

- `apply_preset(preset_name)`
- `rescale(min_value, max_value)`
- `color_mode` (set/get property)
- `scalar_range` (get property)

### IO

The vtk-scene library also provides a convenient factory for creating readers
and writers.

```python
from vtk_scene.io import ReaderFactory

reader = ReaderFactory.create("/path/to/vtk/file.vtu")  # .ex2, vti, vtkhdf, vtp, vtu
```

And similar logic with a writer

```python
from vtk_scene.io import WriterFactory

# .ex2, vti, vtkhdf, vtp, vtu
WriterFactory.write(source, "/path/to/vtk/file.vtu", *preferred_name)
```
