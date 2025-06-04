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
pip install "vtk==9.5.0rc2" --extra-index-url https://wheels.vtk.org
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
