from vtkmodules.vtkIOIOSS import vtkIOSSReader, vtkIOSSWriter

DEFAULT_READER = "IOSS"
DEFAULT_WRITER = "IOSS"

READERS = {
    DEFAULT_READER: vtkIOSSReader,
}

WRITERS = {
    DEFAULT_WRITER: vtkIOSSWriter,
}
