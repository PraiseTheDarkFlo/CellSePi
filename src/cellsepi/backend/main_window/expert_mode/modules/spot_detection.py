import os

import bigfish.detection as detection
import bigfish.plot as plot
import numpy as np
import tifffile

from cellsepi.backend.main_window.expert_mode.module import *
from cellsepi.backend.main_window.expert_mode.pipeline import PipelineRunningException


class SpotDetectionModule(Module, ABC):
    _gui_config = ModuleGuiConfig("SpotDetection",Categories.SEGMENTATION,"This module handles spot detection in cells for each series on the given segmentation_channel with the big-fish python package.")
    def __init__(self, module_id: str) -> None:
        super().__init__(module_id)
        self.inputs = {
            "image_paths": Port("image_paths", dict), #dict[str,dict[str,str]]
            "mask_paths": Port("mask_paths", dict,opt=True),
        }
        self.outputs = {
            "mask_paths": Port("mask_paths", dict), #dict[str,dict[str,str]]
        }
        self.user_remove_duplicate:bool = True
        self.user_use_threshold: bool = False
        self.user_use_log_kernel_and_minimum_distance:bool = False
        self.user_segmentation_channel: str = "2"
        self.user_mask_suffix: str = "_seg"
        self.user_threshold: float = 355.0
        self.user_log_kernel_x: float = 1.456
        self.user_log_kernel_y: float = 1.456
        self.user_log_kernel_z: float = 1.167
        self.user_minimum_distance_x: float = 1.456
        self.user_minimum_distance_y: float = 1.456
        self.user_minimum_distance_z: float = 1.167
        self.user_voxel_size_x: int = 103
        self.user_voxel_size_y: int = 103
        self.user_voxel_size_z: int = 300
        self.user_spot_radius_x: int = 150
        self.user_spot_radius_y: int = 150
        self.user_spot_radius_z: int = 350

    @property
    def settings(self) -> ft.Stack|None:
        if self._settings is not None and self.on_change_user_use_log_kernel_and_minimum_distance() is None:
            self.on_change_user_use_log_kernel_and_minimum_distance = self.update_disable_kernel_distance
            self.on_change_user_use_threshold = self.update_disable_threshold
            self.update_disable_kernel_distance()
            self.update_disable_threshold()
        return self._settings

    def update_disable_threshold(self):
        if self.user_use_threshold:
            self.ref_user_threshold.current.disabled = False
        else:
            self.ref_user_threshold.current.disabled = True

    def update_disable_kernel_distance(self):
        if self.user_use_log_kernel_and_minimum_distance:
            self.ref_user_voxel_size_x.current.disabled = True
            self.ref_user_voxel_size_y.current.disabled = True
            self.ref_user_voxel_size_z.current.disabled = True
            self.ref_user_spot_radius_x.current.disabled = True
            self.ref_user_spot_radius_y.current.disabled = True
            self.ref_user_spot_radius_z.current.disabled = True
            self.ref_user_log_kernel_x.current.disabled = False
            self.ref_user_log_kernel_y.current.disabled = False
            self.ref_user_log_kernel_z.current.disabled = False
            self.ref_user_minimum_distance_x.current.disabled = False
            self.ref_user_minimum_distance_y.current.disabled = False
            self.ref_user_minimum_distance_z.current.disabled = False
        else:
            self.ref_user_voxel_size_x.current.disabled = False
            self.ref_user_voxel_size_y.current.disabled = False
            self.ref_user_voxel_size_z.current.disabled = False
            self.ref_user_spot_radius_x.current.disabled = False
            self.ref_user_spot_radius_y.current.disabled = False
            self.ref_user_spot_radius_z.current.disabled = False
            self.ref_user_log_kernel_x.current.disabled = True
            self.ref_user_log_kernel_y.current.disabled = True
            self.ref_user_log_kernel_z.current.disabled = True
            self.ref_user_minimum_distance_x.current.disabled = True
            self.ref_user_minimum_distance_y.current.disabled = True
            self.ref_user_minimum_distance_z.current.disabled = True

    def run(self):
        image_paths = self.inputs["image_paths"].data
        for iN, image_id in enumerate(list(image_paths)):
            if self.user_segmentation_channel in image_paths[image_id] and os.path.isfile(self.inputs["image_paths"].data[image_id][self.user_segmentation_channel]):
                image_path = self.inputs["image_paths"].data[image_id][self.user_segmentation_channel]
                image = tifffile.imread(image_path)
                if image.ndim == 3:
                    rna = np.transpose(image, (2,1,0)) #z,y,x for big-fish
                else:
                    rna = np.transpose(image, (1,0)) #y,x for big-fish
                try:
                    spots, threshold = detection.detect_spots(rna, remove_duplicate=self.user_remove_duplicate,threshold=None if not self.user_use_threshold else self.user_threshold, return_threshold=True,
                                               voxel_size=(self.user_voxel_size_y,self.user_voxel_size_x) if image.ndim == 2 else (self.user_voxel_size_z,self.user_voxel_size_y,self.user_voxel_size_x), spot_radius=(self.user_spot_radius_y,self.user_spot_radius_x) if image.ndim == 2 else (self.user_spot_radius_z,self.user_spot_radius_y,self.user_spot_radius_x), log_kernel_size=None if not self.user_use_log_kernel_and_minimum_distance else (self.user_log_kernel_y,self.user_log_kernel_x) if image.ndim == 2 else (self.user_log_kernel_z,self.user_log_kernel_y,self.user_log_kernel_x),
                                                          minimum_distance=None if not self.user_use_log_kernel_and_minimum_distance else (self.user_minimum_distance_y,self.user_minimum_distance_x) if image.ndim == 2 else (self.user_minimum_distance_z,self.user_minimum_distance_y,self.user_minimum_distance_x))
                except Exception as e:
                    raise PipelineRunningException("Spot Detection Error",str(e))
                if iN == 0:
                    plot.plot_detection(rna, spots, contrast=True)
