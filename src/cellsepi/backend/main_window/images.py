import multiprocessing
import os
import threading
from concurrent.futures import ThreadPoolExecutor
import pandas as pd

import torch
import numpy as np
from cellpose import models, io
from cellpose.io import imread

from cellsepi.backend.main_window.data_util import load_image_to_numpy
from cellsepi.backend.main_window.notifier import Notifier
from cellsepi.frontend.main_window.gui_mask import reset_mask, handle_mask_update


class BatchImageSegmentation(Notifier):
    """
    This class handles the segmentation of the images.
    """
    def __init__(self,
                 segmentation,
                 gui,
                 device):
        super().__init__()
        self.segmentation = segmentation
        self.gui = gui
        self.device = device
        self.segmentation_channel = self.gui.csp.config.get_bf_channel()
        self.diameter = self.gui.csp.config.get_diameter()
        self.suffix = self.gui.csp.current_mask_suffix
        self.masks_backup = {}
        self.prev_masks_exist = False
        self.num_seg_images = 0
        self.cancel_now = False
        self.pause_now = False
        self.resume_now = False
        self.executor = None
        self.progress_lock = threading.Lock()
        self.progress = 0

    def backup_masks(self):
        """
        This method creates a backup of the previously generated masks.
        """
        self.prev_masks_exist = False

        for image_id, channels in self.gui.csp.mask_paths.items():
            for segmentation_channel, path in channels.items():
                if segmentation_channel == self.segmentation_channel:
                    if os.path.exists(path):
                        self.masks_backup[image_id] = {}
                        self.prev_masks_exist = True
                        mask = np.load(path,allow_pickle=True)
                        self.masks_backup[image_id][segmentation_channel] = mask

        if self.prev_masks_exist:
            for image_id in self.gui.csp.image_paths:
                if image_id not in self.masks_backup:
                    self.masks_backup[image_id] = {}
                    self.masks_backup[image_id][self.segmentation_channel] = None

    def delete_mask(self, path, channels_to_delete, image_id, segmentation_channel):
        if os.path.exists(path):
            channels_to_delete.append((image_id, segmentation_channel))
            if image_id == self.gui.csp.image_id:
                if self.segmentation_channel == segmentation_channel:
                    self.gui.switch_mask.value = False  # sets the mask switch to False because there is no longer a mask
                    self.gui.canvas.container_mask.visible = False  # and sets the mask picture invisible because it is no longer valid
                    reset_mask(self.gui, image_id,segmentation_channel)
                    self.gui.page.update()
            if image_id == self.gui.csp.window_image_id:
               if segmentation_channel == self.gui.csp.window_bf_channel:
                   self.gui.queue.put("delete_mask")  # sends the info that the current image is deleted to the drawing window
            os.remove(path)

    def restore_backup(self):
        """
        This method restores the previously generated masks and deletes the old ones.
        """
        channels_to_delete = []
        if self.prev_masks_exist:
            for image_id, channels in self.masks_backup.items():
                if image_id not in self.gui.csp.mask_paths:
                    self.gui.csp.mask_paths[image_id] = {}
                for segmentation_channel, mask in channels.items():
                    if mask is not None:
                        backup_path = self.gui.csp.mask_paths[image_id].get(segmentation_channel)
                        if backup_path:
                            np.save(backup_path, mask)
                            if image_id == self.gui.csp.window_image_id:
                                if segmentation_channel == self.gui.csp.window_bf_channel:
                                    self.gui.queue.put("refresh_mask")  # refreshes if the backup is the current selected image and the mask is the same channel
                            if image_id == self.gui.csp.image_id and segmentation_channel == self.gui.csp.config.get_bf_channel(): #refreshes or delete the current generated mask
                                handle_mask_update(self.gui)
                            else:
                                reset_mask(self.gui, image_id,segmentation_channel)
                    else:
                        if segmentation_channel in self.gui.csp.mask_paths[image_id]:
                            path = self.gui.csp.mask_paths[image_id][segmentation_channel]
                            self.delete_mask(path, channels_to_delete, image_id, segmentation_channel)
        else:  # case where no masks for this bf_channel existed before
            for image_id, channels in self.gui.csp.mask_paths.items():
                for segmentation_channel, path in channels.items():
                    if segmentation_channel == self.segmentation_channel:
                        self.delete_mask(path, channels_to_delete, image_id, segmentation_channel)

        for image_id, segmentation_channel in channels_to_delete:
            del self.gui.csp.mask_paths[image_id][segmentation_channel]

        for image_id, channel in channels_to_delete:
            del self.gui.csp.mask_paths[image_id]


    # the following methods handle the different actions and handle accordingly
    def cancel_action(self):
        self.cancel_now = True
        if self.executor is not None:
            self.executor.shutdown(wait=True)

    def pause_action(self):
        self.pause_now = True
        if self.executor is not None:
            self.executor.shutdown(wait=True)

    def resume_action(self):
        self.resume_now = True

    def run(self):
        """
        Applies the segmentation model to every image and stores the resulting masks.
        """
        if self.num_seg_images == 0:  # shouldn't backup again, if it was paused and now resuming
            self.backup_masks()
            self.segmentation_channel = self.gui.csp.config.get_bf_channel()
            self.diameter = self.gui.csp.config.get_diameter()
            self.suffix = self.gui.csp.current_mask_suffix
        if self.cancel_now:
            self.cancel_now = False
            self.restore_backup()
            self.num_seg_images = 0
            return
        elif self.pause_now:
            self.pause_now = False
            return
        elif self.resume_now:
            self.resume_now = False
            self.segmentation.is_resuming()

        self._call_start_listeners()
        image_paths = self.gui.csp.image_paths
        segmentation_channel = self.segmentation_channel
        diameter = self.diameter
        suffix = self.suffix

        segmentation_model = self.gui.csp.model_path
        device = torch.device(self.device)  # converts string to device object

        n_images = len(image_paths)

        io.logger_setup()  # configures logging system for Cellpose
        model = models.CellposeModel(device=device, pretrained_model=segmentation_model)

        start_index = self.num_seg_images
        for iN, image_id in enumerate(list(image_paths)[start_index:], start=start_index):
            if segmentation_channel in image_paths[image_id] and os.path.isfile(image_paths[image_id][segmentation_channel]):
                if self.cancel_now:
                    self.cancel_now = False
                    self.restore_backup()
                    self.num_seg_images = 0
                    return
                elif self.pause_now:
                    self.pause_now = False
                    return
                elif self.resume_now:
                    self.resume_now = False
                    self.segmentation.is_resuming()

                image_path = image_paths[image_id][segmentation_channel]
                image = imread(image_path)

                # Normalization
                image = image.astype(np.float32)
                min_val = np.min(image)
                max_val = np.max(image)
                if (max_val - min_val) > 0:
                    image = (image - min_val) / (max_val - min_val)
                else:
                    image = np.zeros_like(image)

                res = model.eval(image, diameter=diameter, channels=[0, 0])
                mask, flow, style = res[:3]

                # Generate the output filename directly using the suffix attribute
                directory, filename = os.path.split(image_path)
                name, _ = os.path.splitext(filename)
                new_filename = f"{name}{suffix}.npy"
                new_path = os.path.join(directory, new_filename)

                default_suffix_path = os.path.splitext(image_path)[0] + '_seg.npy'

                backup_path = None
                if default_suffix_path != new_path:
                    if os.path.exists(default_suffix_path):
                        backup_path = default_suffix_path + '.backup'
                        if os.path.exists(backup_path):
                            os.remove(backup_path)
                        os.rename(default_suffix_path, backup_path)
                # Save the segmentation results directly with the default name first
                io.masks_flows_to_seg([image], [mask], [flow], [image_path])
                if default_suffix_path != new_path:
                    if os.path.exists(default_suffix_path):
                        if os.path.exists(new_path):
                            os.remove(new_path)
                        os.rename(default_suffix_path, new_path)
                        if backup_path is not None:
                            os.rename(backup_path, default_suffix_path)

                if image_id not in self.gui.csp.mask_paths:
                    self.gui.csp.mask_paths[image_id] = {}

                self.gui.csp.mask_paths[image_id][segmentation_channel] = new_path

                progress = str(round((iN + 1) / n_images * 100)) + " %"
                current_image = {"image_id": image_id, "path": image_path}
                self._call_update_listeners(progress, current_image)
                self.num_seg_images = self.num_seg_images + 1
                self.gui.directory.update_mask_check(image_id)
                self.gui.diameter_text.value = self.gui.average_diameter.get_avg_diameter()
            else:
                progress = str(round((iN + 1) / n_images * 100)) + " %"
                current_image = {"image_id": image_id, "path": None}
                self._call_update_listeners(progress, current_image)
                self.num_seg_images = self.num_seg_images + 1

        self._call_completion_listeners()
        # reset variables
        self.num_seg_images = 0

    def run_parallel(self):
        """
        Applies the segmentation model to every image in parallel and stores the resulting masks.
        """
        if self.num_seg_images == 0:  # shouldn't backup again, if it was paused and now resuming
            self.backup_masks()
            self.segmentation_channel = self.gui.csp.config.get_bf_channel()
            self.diameter = self.gui.csp.config.get_diameter()
            self.suffix = self.gui.csp.current_mask_suffix
        if self.cancel_now:
            self.cancel_now = False
            self.restore_backup()
            self.num_seg_images = 0
            return
        elif self.pause_now:
            self.pause_now = False
            return
        elif self.resume_now:
            self.resume_now = False
            self.segmentation.is_resuming()

        self._call_start_listeners()
        image_paths = self.gui.csp.image_paths
        segmentation_channel = self.segmentation_channel
        diameter = self.diameter
        suffix = self.suffix

        segmentation_model = self.gui.csp.model_path
        device = self.device
        device = torch.device(device)  # converts string to device object

        io.logger_setup()  # configures logging system for Cellpose
        model = models.CellposeModel(device=device, pretrained_model=segmentation_model)

        start_index = self.num_seg_images
        self.executor = ThreadPoolExecutor(max_workers=4)
        futures = []
        for iN, image_id in enumerate(list(image_paths)[start_index:], start=start_index):
            futures.append(self.executor.submit(
                self.image_segmentation,
                iN, image_id, image_paths, segmentation_channel, diameter, suffix, model
            ))
        for future in futures:
            future.result()
        if self.cancel_now:
            self.cancel_now = False
            self.restore_backup()
            self.num_seg_images = 0
            return
        self._call_completion_listeners()
        # reset variables
        self.num_seg_images = 0

    def image_segmentation(self,image_id, image_paths, segmentation_channel, diameter, suffix, model):
        """
        Applies the segmentation model to a single image.

        Attributes:
            image_id: identification number of the image
            image_paths: list of image paths
            segmentation_channel: bright field channel
            suffix: suffix to be applied to the mask filename
            model: cellpose model to be used
        """
        n_images = len(image_paths)
        if self.cancel_now:
            self.cancel_now = False
            self.restore_backup()
            self.num_seg_images = 0
            return
        elif self.pause_now:
            self.pause_now = False
            return
        elif self.resume_now:
            self.resume_now = False
            self.segmentation.is_resuming()

        if segmentation_channel in image_paths[image_id] and os.path.isfile(image_paths[image_id][segmentation_channel]):
            image_path = image_paths[image_id][segmentation_channel]
            image = imread(image_path)
            # Normalization
            image = image.astype(np.float32)
            min_val = np.min(image)
            max_val = np.max(image)
            if (max_val - min_val) > 0:
                image = (image - min_val) / (max_val - min_val)
            else:
                image = np.zeros_like(image)

            res = model.eval(image, diameter=diameter, channels=[0, 0])
            mask, flow, style = res[:3]
            # Generate the output filename directly using the suffix attribute
            directory, filename = os.path.split(image_path)
            name, _ = os.path.splitext(filename)
            new_filename = f"{name}{suffix}.npy"
            new_path = os.path.join(directory, new_filename)

            default_suffix_path = os.path.splitext(image_path)[0] + '_seg.npy'
            backup_path = None
            if default_suffix_path != new_path:
                if os.path.exists(default_suffix_path):
                    backup_path = default_suffix_path + '.backup'
                    if os.path.exists(backup_path):
                        os.remove(backup_path)
                    os.rename(default_suffix_path, backup_path)
            # Save the segmentation results directly with the default name first
            io.masks_flows_to_seg([image], [mask], [flow], [image_path])
            if default_suffix_path != new_path:
                if os.path.exists(default_suffix_path):
                    if os.path.exists(new_path):
                        os.remove(new_path)
                    os.rename(default_suffix_path, new_path)
                    if backup_path is not None:
                        os.rename(backup_path, default_suffix_path)
            if image_id not in self.gui.csp.mask_paths:
                self.gui.csp.mask_paths[image_id] = {}

            self.gui.csp.mask_paths[image_id][segmentation_channel] = new_path

            with self.progress_lock:
                self.progress += 1
                percent = round(self.progress / n_images * 100)
                progress = str(percent) + "%"
                current_image = {"image_id": image_id, "path": image_path}
                self._call_update_listeners(progress, current_image)
            self.num_seg_images = self.num_seg_images + 1
            self.gui.directory.update_mask_check(image_id)
            self.gui.diameter_text.value = self.gui.average_diameter.get_avg_diameter()
        else:
            with self.progress_lock:
                self.progress += 1
                percent = round(self.progress / n_images * 100)
                progress = str(percent) + "%"
                current_image = {"image_id": image_id, "path": None}
                self._call_update_listeners(progress, current_image)
            self.num_seg_images = self.num_seg_images + 1

        if self.cancel_now:
            self.cancel_now = False
            self.restore_backup()
            self.num_seg_images = 0
            return
        elif self.pause_now:
            self.pause_now = False
            return
        elif self.resume_now:
            self.resume_now = False
            self.segmentation.is_resuming()


class BatchImageReadout(Notifier):

    def __init__(self, image_paths,
                 mask_paths,
                 segmentation_channel,
                 channel_prefix="c",
                 directory=None):
        super().__init__()

        if directory is None:
            directory = ""

        self.image_paths = image_paths
        self.mask_paths = mask_paths
        self.segmentation_channel = segmentation_channel
        self.channel_prefix = channel_prefix
        self.directory = directory

    def _channel_name(self, channel_id):
        return self.channel_prefix + str(channel_id)

    def run(self):
        self._call_start_listeners()

        image_paths = self.image_paths
        mask_paths = self.mask_paths
        segmentation_channel = self.segmentation_channel

        n_images = len(image_paths)

        row_entries = []

        for iN, image_id in enumerate(image_paths):

            # 1. Check if Image has Mask in mask_paths
            # 2. Iterate over all channels and skip segmentation channel
            # 3. Get Background and derive
            # 4. For each cell readout fluorescence
            # 5. Store values in a pandas dataframe "readout" (Layout: Image ID | Cell ID | Channels ... | Background)

            if not image_id in mask_paths:
                continue
            mask_path = mask_paths[image_id][segmentation_channel]
            mask_data = np.load(mask_path,allow_pickle=True).item()
            mask = mask_data["masks"]

            cell_ids = np.unique(mask)
            if len(cell_ids) == 1:
                continue
            cell_ids = cell_ids[1:]

            channels = list(image_paths[image_id])
            channels.remove(segmentation_channel)
            n_channels = len(channels)

            cur_row_entries = [None] * len(cell_ids)
            for iX, cell_id in enumerate(cell_ids):
                data_entry = {"image_id": image_id,
                              "cell_id": cell_id}
                for channel_id in channels:
                    channel_name = self._channel_name(channel_id)
                    data_entry[channel_name] = None
                    data_entry[f"background {channel_name}"] = None

                cur_row_entries[iX] = data_entry

            for channel_id in channels:
                if channel_id == segmentation_channel:
                    raise Exception("")

                image_path = image_paths[image_id][channel_id]
                channel_name = self._channel_name(channel_id)

                np_image = load_image_to_numpy(image_path)
                background_mask = mask == 0
                background_val = np.mean(np_image[background_mask])

                for iX, cell_id in enumerate(cell_ids):
                    cell_mask = mask == cell_id
                    cell_val = np.mean(np_image[cell_mask])

                    cur_row_entries[iX][channel_name] = cell_val
                    cur_row_entries[iX][f"background {channel_name}"] = background_val

            row_entries += cur_row_entries

            kwargs = {"progress": str(int((iN + 1) / n_images * 100)) + "%",
                      "current_image": {"image_id": image_id}}
            self._call_update_listeners(**kwargs)

        readout_path = os.path.join(self.directory, "readout.xlsx")
        df = pd.DataFrame(row_entries)
        df.to_excel(readout_path, index=False)
        kwargs = {}
        self._call_completion_listeners(readout=df, readout_path=readout_path, **kwargs)
