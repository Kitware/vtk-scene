from pathlib import Path

from vtk_scene.io import decorator, formats

# ---------------------------------------------------------
# TODO:
# - Need to have a time series reader...
# - Allow external registration
# ---------------------------------------------------------


class ReaderFactory:
    @staticmethod
    def klass(file_name, *preferred_name):
        """
        Return reader class for selected filename.
        The set of preferred names will be used for prioritize class resolution.
        """
        if ReaderFactory.can_read(file_name):
            m = formats.get_module_from_suffix(Path(file_name).suffix)
            for reader_name in preferred_name:
                if reader_name in m.READERS:
                    return decorator.add_time_properties(m.READERS[reader_name])
            return decorator.add_time_properties(m.READERS[m.DEFAULT_READER])

        msg = f"Can not read file: {file_name}"
        raise ValueError(msg)

    @staticmethod
    def create(file_name, *preferred_name):
        """
        Return reader instance for selected filename.
        The set of preferred names will be used for prioritize reader resolution.
        """
        klass = ReaderFactory.klass(file_name, *preferred_name)
        return klass(file_name=str(Path(file_name).resolve()))

    @staticmethod
    def read(file_name, *preferred_name):
        """
        Return dataset for selected filename.
        The set of preferred names will be used for prioritize reader resolution.
        """
        reader = ReaderFactory.create(file_name, *preferred_name)
        return reader()

    @staticmethod
    def can_read(file_name):
        """
        Check if the given file suffix could be read.
        """
        m = formats.get_module_from_suffix(Path(file_name).suffix)
        if m is None:
            return False

        return len(m.READERS) > 0

    @property
    def names():
        """
        List available reader names. (i.e. 'VTK XML', 'VTK HDF5', 'IOSS')

        This lookup can be costly as it will import all the vtk modules with readers/writers.
        """
        return formats.extract_reader_names()

    @property
    def suffix():
        """
        List all the supported suffix.
        """
        return [f".{module_name}" for module_name in formats.list_available_modules()]


class WriterFactory:
    @staticmethod
    def klass(file_name, *preferred_name):
        """
        Return writer class for selected filename.
        The set of preferred names will be used for prioritize class resolution.
        """
        if WriterFactory.can_write(file_name):
            m = formats.get_module_from_suffix(Path(file_name).suffix)
            for writer_name in preferred_name:
                if writer_name in m.WRITERS:
                    return m.WRITERS[writer_name]
            return m.WRITERS[m.DEFAULT_WRITER]

        msg = f"Can not write file: {file_name}"
        raise ValueError(msg)

    @staticmethod
    def create(file_name, *preferred_name):
        """
        Return writer instance for selected filename.
        The set of preferred names will be used for prioritize writer resolution.
        """
        klass = ReaderFactory.klass(file_name, *preferred_name)
        return klass(file_name=str(Path(file_name).resolve()))

    @staticmethod
    def write(input, file_name, *preferred_name):
        """
        Write dataset to filename.
        The set of preferred names will be used for prioritize writer resolution.
        """
        writer = WriterFactory.create(file_name, *preferred_name)
        if input.IsA("vtkAlgorithm"):
            writer.input_connection = input.output_port
        elif input.IsA("vtkDataObject"):
            writer.input_data = input
        elif input.IsA("vtkOutputPort"):
            writer.input_connection = input
        else:
            msg = f"Invalid type for input: {input}"
            raise ValueError(msg)
        writer.Write()

    @staticmethod
    def can_write(file_name):
        """
        Check if the given file suffix could be written.
        """
        m = formats.get_module_from_suffix(Path(file_name).suffix)
        if m is None:
            return False

        return len(m.WRITERS) > 0

    @property
    def names():
        """
        List available writer names. (i.e. 'VTK XML', 'VTK HDF5', 'IOSS')

        This lookup can be costly as it will import all the vtk modules with readers/writers.
        """
        return formats.extract_writer_names()

    @property
    def suffix():
        """
        List all the supported suffix.
        """
        return [f".{module_name}" for module_name in formats.list_available_modules()]
