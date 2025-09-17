from os import path

from cellsepi.backend.main_window.data_util import load_directory, ReturnTypePath
from cellsepi.backend.main_window.expert_mode.listener import ProgressEvent
from cellsepi.backend.main_window.expert_mode.module import *
from cellsepi.backend.main_window.images import BatchImageSegmentation, BatchImageReadout
from cellsepi.frontend.main_window.gui_directory import DirectoryCard


class BatchImageReadoutModule(Module, ABC):
    _gui_config = ModuleGuiConfig("BatchImageReadout",Categories.OUTPUTS,"This module handles the readout of the segmented images and saves them in an .xlsx file.")
    def __init__(self, module_id: str) -> None:
        self._module_id = module_id
        self._event_manager: EventManager = None
        self._inputs = {
            "image_paths": Port("image_paths", dict), #dict[str,dict[str,str]]
            "mask_paths": Port("mask_paths", dict), #dict[str,dict[str,str]]
        }
        self._settings: ft.Stack = None
        self.user_directory_path: DirectoryPath = DirectoryPath()
        self.user_segmentation_channel: str = "2"
        self.user_channel_prefix: str = "c"

    @classmethod
    def gui_config(cls) -> ModuleGuiConfig:
       return cls._gui_config

    @property
    def module_id(self) -> str:
        return self._module_id

    @module_id.setter
    def module_id(self,value: str):
        self._module_id = value

    @property
    def inputs(self) -> dict[str, Port]:
        return self._inputs

    @property
    def outputs(self) -> dict[str, Port]:
        return {}

    @property
    def settings(self) -> ft.Stack:
        return self._settings

    @property
    def event_manager(self) -> EventManager:
        return self._event_manager

    @event_manager.setter
    def event_manager(self, value: EventManager):
        self._event_manager = value

    def run(self):
        BatchImageReadout(self.inputs["image_paths"].data, self.inputs["mask_paths"].data,self.user_segmentation_channel,self.user_channel_prefix,self.user_directory_path.path,True).run(self.event_manager)