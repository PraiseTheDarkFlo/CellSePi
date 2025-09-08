import os

import numpy as np
from cv2 import imread
from tifffile import tifffile
from PIL import Image

from cellsepi.backend.main_window.data_util import load_directory, ReturnTypePath
from cellsepi.backend.main_window.expert_mode.listener import ProgressEvent
from cellsepi.backend.main_window.expert_mode.module import *
from cellsepi.backend.main_window.images import BatchImageSegmentation
from cellsepi.frontend.main_window.gui_directory import DirectoryCard


class Project3dTo2d(Module, ABC):
    _gui_config = ModuleGuiConfig("Project3Dto2D",Categories.FILTERS,"This modules handles the conversion from 3D data to 2D data based on an max z projection.")
    def __init__(self, module_id: str) -> None:
        self._module_id = module_id
        self._event_manager: EventManager = None
        self._inputs = {
            "image_paths": Port("image_paths", dict), #dict[str,dict[str,str]]
        }
        self._outputs = {
            "image_paths": Port("image_paths", dict), #dict[str,dict[str,str]]
        }
        self._settings: ft.CupertinoBottomSheet = None

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
    def settings(self) -> ft.CupertinoBottomSheet:
        return self._settings

    @property
    def event_manager(self) -> EventManager:
        return self._event_manager

    @event_manager.setter
    def event_manager(self, value: EventManager):
        self._event_manager = value

    def run(self):
        images = self.inputs["image_paths"].data
        outputs_images = {}
        n_series = len(images)
        self.event_manager.notify(ProgressEvent(percent=0, process=f"Projecting Series: Starting"))
        for iN,series in enumerate(images):
            outputs_images[series] = {}
            for channel in images[series]:
                image_path = images[series][channel]
                image = tifffile.imread(image_path) #dimensions are: X, Y, Z
                image_max = np.max(image,axis=2)
                base_dir = os.path.dirname(image_path)
                proj_dir = os.path.join(base_dir, "projections")
                os.makedirs(proj_dir, exist_ok=True)
                name =os.path.basename(image_path)
                new_path = os.path.join(proj_dir, name)
                image_max_8bit = ((image_max - image_max.min()) / (image_max.max() - image_max.min()) * 255).astype(np.uint8)
                img8 = Image.fromarray(image_max_8bit)
                img8.save(new_path, format="TIFF")
                outputs_images[series][channel] = new_path

            self.event_manager.notify(ProgressEvent(percent=int((iN+1) / n_series * 100), process=f"Projecting Series: {iN+1}/{n_series}"))
        self.outputs["image_paths"].data = outputs_images
        self.event_manager.notify(ProgressEvent(percent=100, process=f"Projecting Series: Finished"))




