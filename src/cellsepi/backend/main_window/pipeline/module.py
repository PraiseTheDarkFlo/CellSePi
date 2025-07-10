from abc import ABC, abstractmethod
import flet as ft

class Port:
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