from vtkmodules.vtkIOXML import (
    vtkXMLImageDataReader,
    vtkXMLImageDataWriter,
)

DEFAULT_READER = "VTK XML"
DEFAULT_WRITER = "VTK XML"

READERS = {
    DEFAULT_READER: vtkXMLImageDataReader,
}

WRITERS = {
    DEFAULT_WRITER: vtkXMLImageDataWriter,
}
