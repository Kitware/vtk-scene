from vtkmodules.vtkIOHDF import vtkHDFReader, vtkHDFWriter

DEFAULT_READER = "VTK HDF5"
DEFAULT_WRITER = "VTK HDF5"

READERS = {
    DEFAULT_READER: vtkHDFReader,
}

WRITERS = {
    DEFAULT_WRITER: vtkHDFWriter,
}
