from vtkmodules.vtkIOXML import (
    vtkXMLUnstructuredGridReader,
    vtkXMLUnstructuredGridWriter,
)

DEFAULT_READER = "VTK XML"
DEFAULT_WRITER = "VTK XML"

READERS = {
    DEFAULT_READER: vtkXMLUnstructuredGridReader,
}

WRITERS = {
    DEFAULT_WRITER: vtkXMLUnstructuredGridWriter,
}
