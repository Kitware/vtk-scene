from vtkmodules.vtkCommonDataModel import vtkDataObject
from vtkmodules.vtkCommonExecutionModel import vtkStreamingDemandDrivenPipeline


def get_time_steps(self):
    self.UpdateInformation()
    oi = self.GetOutputInformation(0)
    return oi.Get(vtkStreamingDemandDrivenPipeline.TIME_STEPS())


def get_time_value(self):
    return self().GetInformation().Get(vtkDataObject.DATA_TIME_STEP())


def add_time_properties(klass):
    class_name = f"Py{klass.__name__}"
    class_dict = {
        "time_values": property(get_time_steps),
        "time_value": property(get_time_value),
    }
    return type(class_name, (klass,), class_dict)


__all__ = [
    "add_time_properties",
]
