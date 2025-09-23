from cellsepi.backend.main_window.data_util import load_directory, ReturnTypePath
from cellsepi.backend.main_window.expert_mode.module import *
from cellsepi.frontend.main_window.gui_directory import DirectoryCard


class ReadLif(Module,ABC):
    _gui_config = ModuleGuiConfig("ReadLif",Categories.INPUTS,"This module handles the read in of .lif files and if available reads in the mask of the images.")
    def __init__(self, module_id: str) -> None:
        self._module_id = module_id
        self._event_manager: EventManager = None
        self._outputs = {
            "image_paths": Port("image_paths", dict),
            "mask_paths": Port("mask_paths", dict),
        }
        self._settings: ft.Stack = None
        self.user_file_path: FilePath = FilePath(suffix=["lif"])
        self.user_channel_prefix: str = "c"
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
        return {}

    @property
    def outputs(self) -> dict[str, Port]:
        return self._outputs

    @property
    def settings(self) -> ft.Stack:
        return self._settings

    @property
    def on_settings_dismiss(self):
        return

    def finished(self):
        pass

    @property
    def event_manager(self) -> EventManager:
        return self._event_manager

    @event_manager.setter
    def event_manager(self, value: EventManager):
        self._event_manager = value

    def run(self):
        working_directory = DirectoryCard().select_directory_parallel(self.user_file_path.path, True, self.user_channel_prefix, self.event_manager)
        self._outputs["image_paths"].data,self._outputs["mask_paths"].data= load_directory(working_directory, self.user_channel_prefix, self.user_mask_suffix, ReturnTypePath.BOTH_PATHS, self.event_manager)