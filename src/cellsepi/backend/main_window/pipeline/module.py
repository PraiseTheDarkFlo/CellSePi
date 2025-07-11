from abc import ABC, abstractmethod
import flet as ft
from typing import List

class Port:
    """
    Ports defines an input or output of a module.
    Ports with the same names in different modules are considered as the same type of ports
    and their data can be transferred with pipes to each other.
    """
    def __init__(self, name: str, data_type: type, opt: bool = False):
        self.name = name
        self.data_type = data_type #type
        self.opt = opt #optional
        self._data = None

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, value):
        if isinstance(value, self.data_type) or value is None:
            self._data = value
        else:
            raise TypeError(f"Expected data of type {self.data_type}, got {type(value)}!")


class Module(ABC):
    """
    Modules are independent processes within the pipeline that perform a specific task.
    The modules should be designed to function independently of other modules,
    as long as the correct inputs are provided.
    """
    #name for the gui
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    #the needed inputs of the module
    @property
    @abstractmethod
    def inputs(self) -> dict[str, Port]:
        pass

    def get_mandatory_inputs(self) -> List[str]:
        """
        Returns the list of names of input ports that are required by the module.
        """
        mandatory_inputs = []
        for port in self.inputs.values():
            if not port.opt:
                mandatory_inputs.append(port.name)
        return mandatory_inputs

    #the needed outputs of the module
    @property
    @abstractmethod
    def outputs(self) -> dict[str, Port]:
        pass

    #the provided gui from the module
    @property
    @abstractmethod
    def gui(self) -> ft.Container:
        pass

    @abstractmethod
    def run(self):
        pass

