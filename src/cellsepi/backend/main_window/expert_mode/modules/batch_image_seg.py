
from cellsepi.backend.main_window.data_util import load_directory, ReturnTypePath
from cellsepi.backend.main_window.expert_mode.listener import ProgressEvent
from cellsepi.backend.main_window.expert_mode.module import *
from cellsepi.backend.main_window.expert_mode.pipeline import PipelineRunningException
from cellsepi.backend.main_window.images import BatchImageSegmentation
from cellsepi.frontend.main_window.gui_directory import DirectoryCard


class BatchImageSegModule(Module, ABC):
    _gui_config = ModuleGuiConfig("BatchImageSeg",Categories.SEGMENTATION,"This module handles the segmentation of cells for each series on the given segmentation_channel with the provided model in model_path.")
    def __init__(self, module_id: str) -> None:
        self._module_id = module_id
        self._event_manager: EventManager = None
        self._inputs = {
            "image_paths": Port("image_paths", dict), #dict[str,dict[str,str]]
            "mask_paths": Port("mask_paths", dict,opt=True), #dict[str,dict[str,str]]
        }
        self._outputs = {
            "mask_paths": Port("mask_paths", dict), #dict[str,dict[str,str]]
        }
        self._settings: ft.Stack = None
        self.user_model_path: FilePath = FilePath()
        self.user_segmentation_channel: str = "2"
        self.user_diameter: float = 125.0
        self.user_mask_suffix: str = "_seg"

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
        return self._outputs

    @property
    def settings(self) -> ft.Stack:
        return self._settings

    def finished(self):
        pass

    @property
    def on_settings_dismiss(self):
        return None

    @property
    def event_manager(self) -> EventManager:
        return self._event_manager

    @event_manager.setter
    def event_manager(self, value: EventManager):
        self._event_manager = value

    def run(self):
        if self.inputs["mask_paths"].data is None:
            self.inputs["mask_paths"].data = {}
        try:
            BatchImageSegmentation(segmentation_channel=self.user_segmentation_channel,diameter=self.user_diameter,suffix=self.user_mask_suffix).run(self.event_manager,self.inputs["image_paths"].data,self.inputs["mask_paths"].data,self.user_model_path.path)
        except:
            raise PipelineRunningException("Segmentation Error", "Incompatible file for the segmentation model.")

        self.outputs["mask_paths"].data = self.inputs["mask_paths"].data

