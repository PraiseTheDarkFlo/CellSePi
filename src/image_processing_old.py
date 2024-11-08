import matplotlib.pyplot as plt
import torch
import numpy as np
from cellpose import models, io
from cellpose.io import imread

from data_util_old import load_image_to_numpy
import pandas as pd


class Notifier:

    def __init__(self):
        self._start_listeners = set()
        self._update_listeners = set()
        self._completion_listeners = set()

    def _call_listeners(self, listeners, args, kwargs):
        for listener in listeners:
            listener(*args, **kwargs)

    def add_start_listener(self, listener):
        self._start_listeners.add(listener)

    def remove_start_listener(self, listener):
        self._start_listeners.remove(listener)

    def _call_start_listeners(self, *args, **kwargs):
        self._call_listeners(self._start_listeners, args, kwargs)

    def add_update_listener(self, listener):
        self._update_listeners.add(listener)

    def remove_update_listener(self, listener):
        self._update_listeners.remove(listener)

    def _call_update_listeners(self, *args, **kwargs):
        self._call_listeners(self._update_listeners, args, kwargs)

    def add_completion_listener(self, listener):
        self._completion_listeners.add(listener)

    def remove_completion_listener(self, listener):
        self._completion_listeners.remove(listener)

    def _call_completion_listeners(self, *args, **kwargs):
        self._call_listeners(self._completion_listeners, args, kwargs)


class BatchImageSegmentation(Notifier):

    def __init__(self, image_paths,
                 segmentation_channel,
                 diameter=250,
                 device=None,
                 segmentation_model=None):
        super().__init__()

        if device is None:
            device = "cpu"

        self.image_paths = image_paths
        self.segmentation_channel = segmentation_channel
        self.diameter = diameter
        self.device = device
        self.segmentation_model = segmentation_model

    def run(self):
        self._call_start_listeners()

        image_paths = self.image_paths
        segmentation_channel = self.segmentation_channel
        diameter = self.diameter

        segmentation_model = self.segmentation_model
        device = self.device
        device = torch.device(device)

        segmentation_model = "models/CP_20240715_171241"

        n_images = len(image_paths)

        io.logger_setup()
        # model_type='cyto' or 'nuclei' or 'cyto2' or 'cyto3'
        # model = models.Cellpose(model_type="cyto3", device=device)
        model = models.CellposeModel(device=device, pretrained_model=segmentation_model)

        # images = [imread(image_paths[image_id][segmentation_channel]) for image_id in image_paths]

        # res = model.eval(images, diameter=diameter, channels=[[0, 0]])

        mask_paths = {}
        for iN, image_id in enumerate(image_paths):
            image_path = image_paths[image_id][segmentation_channel]

            image = imread(image_path)

            res = model.eval(image, diameter=diameter, channels=[0, 0])
            mask, flow, style = res[:3]

            io.masks_flows_to_seg([image], [mask], [flow], [image_path])
            """ 
            Report current state
            """
            kwargs = {"progress": (iN + 1) / n_images * 100,
                      "current_image": {"image_id": image_id,
                                        "path": image_path}}
            self._call_update_listeners(**kwargs)

        kwargs = {}
        self._call_completion_listeners(mask_paths, **kwargs)


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

            # ToDo
            # 1. Check if Image has Mask in mask_paths
            # 2. Iterate over all channels and skip segmentation channel
            # 3. Get Background and derive
            # 4. For each cell readout fluorescence
            # 5. Store values in a pandas dataframe "readout" (Layout: Image ID | Cell ID | Channels ... | Background)

            if not image_id in mask_paths:
                continue

            mask_path = mask_paths[image_id][segmentation_channel]
            mask_data = np.load(mask_path, allow_pickle=True).item()
            mask = mask_data["masks"]

            cell_ids = np.unique(mask)
            if len(cell_ids) == 1:
                print(f"Skipping image {image_id} as no cells are present.")
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
                    continue

                image_path = image_paths[image_id][channel_id]
                channel_name = self._channel_name(channel_id)

                np_image = load_image_to_numpy(image_path)
                background_mask = mask == 0
                background_val = np.mean(np_image[background_mask])

                # fig, axes = plt.subplots(ncols = 2)
                # axes[0].imshow(np_image)
                # axes[1].imshow(background_mask)
                # plt.show()
                # print(background_val)

                for iX, cell_id in enumerate(cell_ids):
                    cell_mask = mask == cell_id
                    cell_val = np.mean(np_image[cell_mask])

                    cur_row_entries[iX][channel_name] = cell_val
                    cur_row_entries[iX][f"background {channel_name}"] = background_val

                # Image ID | Cell ID | Channels ... | Background

                pass
            pass

            row_entries += cur_row_entries

            """ 
            Report current state
            """
            kwargs = {"progress": (iN + 1) / n_images * 100,
                      "current_image": {"image_id": image_id}}
            self._call_update_listeners(**kwargs)

        readout_path = self.directory / "readout.xlsx"
        df = pd.DataFrame(row_entries)
        df.to_excel(readout_path, index=False)
        kwargs = {}
        self._call_completion_listeners(readout=df, readout_path=readout_path, **kwargs)
