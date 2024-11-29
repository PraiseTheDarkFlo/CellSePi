import os

import matplotlib.pyplot as plt
import torch
import numpy as np
from cellpose import models, io
from cellpose.io import imread

#from data_util import load_image_to_numpy
import pandas as pd

from notifier import Notifier


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
        #TODO zu jedem Zeitpunkt einen Listener, ob gestoppt werden soll
        self._call_start_listeners()

        image_paths = self.image_paths
        segmentation_channel = self.segmentation_channel
        diameter = self.diameter

        segmentation_model = self.segmentation_model
        device = self.device
        device = torch.device(device)


        #n_images = len(image_paths)

        io.logger_setup()
        # model_type='cyto' or 'nuclei' or 'cyto2' or 'cyto3'
        # model = models.Cellpose(model_type="cyto3", device=device)
        model = models.CellposeModel(device=device, pretrained_model=segmentation_model)

        # images = [imread(image_paths[image_id][segmentation_channel]) for image_id in image_paths]

        # res = model.eval(images, diameter=diameter, channels=[[0, 0]])
        kwargs = {}
        mask_paths = {}
        for iN in range(2):
            # for iN, image_id in enumerate(image_paths):
            # image_path = image_paths[image_id][segmentation_channel]
            if iN == 0:
                image_path = "/Users/nikedratt/Downloads/data/04072024_HEK293_CellMaskDR_01/xy01c1.tif"
            if iN == 1:
                image_path = "/Users/nikedratt/Downloads/data/04072024_HEK293_CellMaskDR_01/xy01c2.tif"

            image = imread(image_path)

            res = model.eval(image, diameter=diameter, channels=[0, 0])
            mask, flow, style = res[:3]

            #TODO output benennung muss variabel sein (nicht immer _seg)
            io.masks_flows_to_seg([image], [mask], [flow], [image_path])

            directory, filename = os.path.split(image_path)
            name, _ = os.path.splitext(filename)
            new_filename = f"{name}_seg.npy"
            mask_paths.update({str(iN): os.path.join(directory, new_filename)})
            print(mask_paths.get(str(iN)))
            """ 
            Report current state
            """

            kwargs = {"progress": (iN + 1) / 2 * 100,
                      "current_image": {"image_id": iN,
                                        "path": image_path}}
            self._call_update_listeners(str(round(kwargs.get("progress")))+" %")

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
