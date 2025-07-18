from abc import ABC, abstractmethod
from collections import deque
from enum import Enum

import flet as ft
from typing import List

from cellsepi.backend.main_window.expert_mode.event_manager import EventManager


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
        """
        Raises:
            TypeError: If the data type is not the required type.
        """
        if isinstance(value, self.data_type) or value is None:
            self._data = value
        else:
            raise TypeError(f"Expected data of type {self.data_type}, got {type(value)}!")

class Categories(Enum):
    INPUTS = ft.Colors.ORANGE
    OUTPUTS = ft.Colors.LIGHT_BLUE
    FILTERS = ft.Colors.PURPLE
    SEGMENTATION = ft.Colors.YELLOW

class GuiConfig:
    def __init__(self, name: str, category: Categories, description:str = None):
        self.name = name
        self.category = category
        self.description = description

class IdManager:
    """
    Manages the module ID's so every module
    """
    def __init__(self):
        self._free_ids_queue = deque()
        self.current_id = 0

    def get_id(self) -> int:
        if len(self._free_ids_queue) > 0:
            return self._free_ids_queue.popleft()
        else:
            id_number = self.current_id
            self.current_id += 1
            return id_number

    def free_id(self, id_number: int) -> None:
        self._free_ids_queue.append(id_number)


class Module(ABC):
    """
    Modules are independent processes within the pipeline that perform a specific task.
    The modules should be designed to function independently of other modules,
    as long as the correct inputs are provided.
    """

    @classmethod
    def get_id(cls) -> int:
        if not hasattr(cls, "_id_manager"):
            cls._id_manager = IdManager()
        return cls._id_manager.get_id()

    @classmethod
    def free_id(cls, id_number: int):
        if hasattr(cls, "_id_manager"):
            cls._id_manager.free_id(id_number)

    @classmethod
    def destroy_id_manager(cls):
        if hasattr(cls, "_id_manager"):
            del cls._id_manager

    @classmethod
    @abstractmethod
    def get_gui_config(cls) -> GuiConfig:
       pass

    @abstractmethod
    def __init__(self,module_id: str):
        pass

    def destroy(self):
        id_number = self.module_id.removeprefix(self.get_gui_config().name)
        if id_number != "":
            number = int(id_number)
            self.free_id(number)

    #module_id for the gui
    @property
    @abstractmethod
    def module_id(self) -> str:
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

    @property
    @abstractmethod
    def settings(self) -> ft.Container:
        """
        The settings window of the module in the gui.
        """
        pass


    @property
    @abstractmethod
    def event_manager(self) -> EventManager:
        pass

    @event_manager.setter
    @abstractmethod
    def event_manager(self, value: EventManager):
        pass


    @abstractmethod
    def run(self):
        pass

