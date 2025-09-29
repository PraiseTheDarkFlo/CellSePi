import os

from skimage.morphology import ball, disk, dilation, erosion
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
        self.user_spot_radius_pixels: float = 3.0
        self.user_log_kernel_x_pixels: float = 1.456
        self.user_log_kernel_y_pixels: float = 1.456
        self.user_log_kernel_z_pixels: float = 1.167
        self.user_minimum_distance_x_pixels: float = 1.456
        self.user_minimum_distance_y_pixels: float = 1.456
        self.user_minimum_distance_z_pixels: float = 1.167
        self.user_voxel_size_x_nm: float = 103.0
        self.user_voxel_size_y_nm: float = 103.0
        self.user_voxel_size_z_nm: float = 300.0
        self.user_spot_radius_x_nm: float = 150.0
        self.user_spot_radius_y_nm: float = 150.0
        self.user_spot_radius_z_nm: float = 350.0

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
            self.ref_user_voxel_size_x_nm.current.disabled = True
            self.ref_user_voxel_size_y_nm.current.disabled = True
            self.ref_user_voxel_size_z_nm.current.disabled = True
            self.ref_user_spot_radius_x_nm.current.disabled = True
            self.ref_user_spot_radius_y_nm.current.disabled = True
            self.ref_user_spot_radius_z_nm.current.disabled = True
            self.ref_user_spot_radius_pixels.current.disabled = False
            self.ref_user_log_kernel_x_pixels.current.disabled = False
            self.ref_user_log_kernel_y_pixels.current.disabled = False
            self.ref_user_log_kernel_z_pixels.current.disabled = False
            self.ref_user_minimum_distance_x_pixels.current.disabled = False
            self.ref_user_minimum_distance_y_pixels.current.disabled = False
            self.ref_user_minimum_distance_z_pixels.current.disabled = False
        else:
            self.ref_user_voxel_size_x_nm.current.disabled = False
            self.ref_user_voxel_size_y_nm.current.disabled = False
            self.ref_user_voxel_size_z_nm.current.disabled = False
            self.ref_user_spot_radius_x_nm.current.disabled = False
            self.ref_user_spot_radius_y_nm.current.disabled = False
            self.ref_user_spot_radius_z_nm.current.disabled = False
            self.ref_user_spot_radius_pixels.current.disabled = True
            self.ref_user_log_kernel_x_pixels.current.disabled = True
            self.ref_user_log_kernel_y_pixels.current.disabled = True
            self.ref_user_log_kernel_z_pixels.current.disabled = True
            self.ref_user_minimum_distance_x_pixels.current.disabled = True
            self.ref_user_minimum_distance_y_pixels.current.disabled = True
            self.ref_user_minimum_distance_z_pixels.current.disabled = True

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
                    spots, threshold = detection.detect_spots(rna, remove_duplicate=self.user_remove_duplicate, threshold=None if not self.user_use_threshold else self.user_threshold, return_threshold=True,
                                                              voxel_size=(self.user_voxel_size_y_nm, self.user_voxel_size_x_nm) if image.ndim == 2 else (self.user_voxel_size_z_nm, self.user_voxel_size_y_nm, self.user_voxel_size_x_nm), spot_radius=(self.user_spot_radius_y_nm, self.user_spot_radius_x_nm) if image.ndim == 2 else (self.user_spot_radius_z_nm, self.user_spot_radius_y_nm, self.user_spot_radius_x_nm), log_kernel_size=None if not self.user_use_log_kernel_and_minimum_distance else (self.user_log_kernel_y_pixels, self.user_log_kernel_x_pixels) if image.ndim == 2 else (self.user_log_kernel_z_pixels, self.user_log_kernel_y_pixels, self.user_log_kernel_x_pixels),
                                                              minimum_distance=None if not self.user_use_log_kernel_and_minimum_distance else (self.user_minimum_distance_y_pixels, self.user_minimum_distance_x_pixels) if image.ndim == 2 else (self.user_minimum_distance_z_pixels, self.user_minimum_distance_y_pixels, self.user_minimum_distance_x_pixels))
                except Exception as e:
                    raise PipelineRunningException("Spot Detection Error",str(e))

                if self.user_use_log_kernel_and_minimum_distance:
                    radius_px = self.user_spot_radius_pixels
                else:
                    if image.ndim == 3:
                        radius_px = tuple(r / v for r, v in zip((self.user_spot_radius_z_nm, self.user_spot_radius_y_nm,
                                                                 self.user_spot_radius_x_nm),
                                                                (self.user_voxel_size_z_nm, self.user_voxel_size_y_nm,
                                                                 self.user_voxel_size_x_nm)))
                    else:
                        radius_px = tuple(r / v for r, v in zip((self.user_spot_radius_y_nm,
                                                                 self.user_spot_radius_x_nm),
                                                                (self.user_voxel_size_y_nm,
                                                                 self.user_voxel_size_x_nm)))
                if iN == 0:
                    print("1")
                    radius_mean = np.mean(radius_px)
                    plot.plot_detection(rna, spots,radius=radius_mean, contrast=True)
                    print("2")