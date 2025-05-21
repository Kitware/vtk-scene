from vtkmodules.vtkIOXML import (
    vtkXMLPolyDataReader,
    vtkXMLPolyDataWriter,
)

DEFAULT_READER = "VTK XML"
DEFAULT_WRITER = "VTK XML"

READERS = {
    DEFAULT_READER: vtkXMLPolyDataReader,
}

WRITERS = {
    DEFAULT_WRITER: vtkXMLPolyDataWriter,
}
