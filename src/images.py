import os

import matplotlib.pyplot as plt
import torch
import numpy as np
from cellpose import models, io
from cellpose.io import imread

from data_util import load_image_to_numpy
import pandas as pd

from notifier import Notifier


class BatchImageSegmentation(Notifier):

    def __init__(self, image_paths,
                 segmentation_channel,
                 diameter=250,
                 device=None,
                 segmentation_model=None,
                 suffix="_seg"):
        super().__init__()

        if device is None:
            device = "cpu"

        self.image_paths = image_paths
        self.segmentation_channel = segmentation_channel
        self.diameter = diameter
        self.device = device
        self.segmentation_model = segmentation_model
        self.suffix = suffix  # New suffix attribute

    def run(self):
        # TODO zu jedem Zeitpunkt einen Listener, ob gestoppt werden soll
        self._call_start_listeners()

        image_paths = self.image_paths
        segmentation_channel = self.segmentation_channel
        diameter = self.diameter

        segmentation_model = self.segmentation_model
        device = self.device
        device = torch.device(device)

        n_images = len(image_paths)

        io.logger_setup()
        model = models.CellposeModel(device=device, pretrained_model=segmentation_model)

        kwargs = {}
        mask_paths = {}
        for iN, image_id in enumerate(image_paths):
            image_path = image_paths[image_id][segmentation_channel]
            image = imread(image_path)

            res = model.eval(image, diameter=diameter, channels=[0, 0])
            mask, flow, style = res[:3]

            # Generate the output filename directly using the suffix attribute
            directory, filename = os.path.split(image_path)
            name, _ = os.path.splitext(filename)
            new_filename = f"{name}{self.suffix}.npy"
            new_path = os.path.join(directory, new_filename)

            # Save the segmentation results directly with the new filename
            io.masks_flows_to_seg([image], [mask], [flow], [image_path])
            mask_paths.update({str(iN): new_path})
            print(mask_paths.get(str(iN)))

            kwargs = {"progress": str(round((iN + 1) / n_images * 100)) + "%",
                      "current_image": {"image_id": iN, "path": image_path}}
            self._call_update_listeners(kwargs.get("progress"), kwargs.get("current_image"))

        # TODO hier muss ein listener hin, der schaut ob gestoppt werden muss
        self._call_completion_listeners(mask_paths)


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
