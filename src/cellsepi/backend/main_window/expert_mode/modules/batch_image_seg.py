from os import path

from cellsepi.backend.main_window.data_util import load_directory, ReturnTypePath
from cellsepi.backend.main_window.expert_mode.module import *
from cellsepi.backend.main_window.images import BatchImageSegmentation
from cellsepi.frontend.main_window.gui_directory import DirectoryCard


class BatchImageSegModule(Module, ABC):
    _gui_config = ModuleGuiConfig("BatchImageSegModule",Categories.SEGMENTATION,"")
    def __init__(self, module_id: str) -> None:
        self._module_id = module_id
        self._event_manager: EventManager = None
        self._inputs = {
            "image_paths": Port("image_paths", dict), #dict[str,dict[str,str]]
            "mask_paths": Port("mask_paths", dict) #dict[str,dict[str,str]]
        }
        self._outputs = {
            "mask_paths": Port("mask_paths", dict) #dict[str,dict[str,str]]
        }
        self._settings: ft.Container = None #TODO: gui setting for module
        self._directory_path: str = ""
        self._segmentation_channel: str = "2"
        self._diameter: float = 125.0
        self._ms: str = "_seg"
        self._model_path: path

    @classmethod
    def gui_config(cls) -> ModuleGuiConfig:
       return cls._gui_config

    @property
    def module_id(self) -> str:
        return self._module_id

    @property
    def inputs(self) -> dict[str, Port]:
        return self._inputs

    @property
    def outputs(self) -> dict[str, Port]:
        return self._outputs

    @property
    def settings(self) -> ft.Container:
        return self._settings

    @property
    def event_manager(self) -> EventManager:
        return self._event_manager

    @event_manager.setter
    def event_manager(self, value: EventManager):
        self._event_manager = value

    def run(self):
        BatchImageSegmentation(segmentation_channel=self._segmentation_channel,diameter=self._diameter,suffix=self._ms).run(self.event_manager,self.inputs["image_paths"].data,self.inputs["mask_paths"].data)
        self._outputs["mask_paths"].data = self.inputs["mask_paths"].data