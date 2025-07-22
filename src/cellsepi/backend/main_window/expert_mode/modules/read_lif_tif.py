from cellsepi.backend.main_window.data_util import load_directory, ReturnTypePath
from cellsepi.backend.main_window.expert_mode.module import *
from cellsepi.frontend.main_window.gui_directory import DirectoryCard


class ReadLifTif(Module,ABC):
    _gui_config = ModuleGuiConfig("ReadLifTif",Categories.INPUTS,"")
    def __init__(self, module_id: str) -> None:
        self._module_id = module_id
        self._event_manager: EventManager = None
        self._outputs = {
            "image_paths": Port("image_paths", dict[str,dict[str,str]]),
            "mask_paths": Port("mask_paths", dict[str,dict[str,str]])
        }
        self._settings: ft.Container = None #TODO: gui setting for module
        self._directory_path: str = ""
        self._lif: bool = False
        self._cp: str = "c"
        self._ms: str = "_seg"

    @classmethod
    def gui_config(cls) -> ModuleGuiConfig:
       return cls._gui_config

    @property
    def module_id(self) -> str:
        return self._module_id

    @property
    def inputs(self) -> dict[str, Port]:
        return {}

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
        working_directory = DirectoryCard().select_directory_parallel(self._directory_path,self._lif,self._cp,self.event_manager)
        self._outputs["image_paths"],self._outputs["mask_paths"]= load_directory(working_directory,self._cp,self._ms,ReturnTypePath.BOTH_PATHS,self.event_manager)