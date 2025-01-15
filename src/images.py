import os
from concurrent.futures import ThreadPoolExecutor

import torch
import numpy as np
from cellpose import models, io
from cellpose.io import imread

from src.data_util import load_image_to_numpy
import pandas as pd
from time import time
from src import notifier
from src.notifier import Notifier

class BatchImageSegmentation(Notifier):

    def __init__(self,
                 segmentation,
                 csp,
                 device=None):
        super().__init__()
        # TODO REVIEW by Flo: was ist mit device ist auch GPU möglich dann
        #  in seg auch irgendwie aktivieren lassen? einfach komisch
        #  das davor in seg auf cpu fest gesetzt wird und hier nochmal
        #  falls nicht none auch wieder gesetzt hätte es wenn nicht überprüft
        #  wahrscheinlich einfach nicht device mit gegeben so dass das hier auslöst:
        if device is None:
            device = "cpu"

        self.segmentation = segmentation
        self.csp = csp
        self.device = device
        # TODO REVIEW by Flo: ich würde entweder alle Statis drausen bei Segmentation machen oder alles hier bzw. oder sogar in csp?
        self.cancel_now = False
        self.pause_now = False
        self.resume_now = False

    def cancel_action(self):
        self.cancel_now = True

    def pause_action(self):
        self.pause_now = True

    def resume_action(self):
        self.resume_now = True

    """
    Apply the segmentation model to every image
    """
    def run(self):
        if self.cancel_now:
            pass
        elif self.pause_now:
            pass
        elif self.resume_now:
            pass
        self._call_start_listeners()
        image_paths = self.csp.image_paths
        segmentation_channel = self.csp.config.get_bf_channel()
        print(segmentation_channel)
        print(image_paths)
        diameter = self.csp.config.get_diameter()
        suffix = self.csp.config.get_mask_suffix()

        segmentation_model = self.csp.model_path
        device = torch.device(self.device) # converts string to device object

        n_images = len(image_paths)

        io.logger_setup() # configures logging system for Cellpose
        model = models.CellposeModel(device=device, pretrained_model=segmentation_model)

        start_time_sequential= time()
        for iN, image_id in enumerate(image_paths):
            if self.cancel_now:
                self._call_cancel_listeners()
                return
            elif self.pause_now:
                self._call_pause_listeners()
                return
            elif self.resume_now:
                self._call_resume_listeners()
                return

            image_path = image_paths[image_id][segmentation_channel]
            image = imread(image_path)

            res = model.eval(image, diameter=diameter, channels=[0, 0])
            mask, flow, style = res[:3]

            # Generate the output filename directly using the suffix attribute
            directory, filename = os.path.split(image_path)
            name, _ = os.path.splitext(filename)
            new_filename = f"{name}{suffix}.npy"
            new_path = os.path.join(directory, new_filename)

            # Save the segmentation results directly with the default name first
            io.masks_flows_to_seg([image], [mask], [flow], [image_path])

            # Rename the file to the desired name
            # TODO REVIEW by Flo: umbennen hat halt nachteil fällt mir gerade ein,
            #  dass wenn wir segs schon haben diese überschrieben werden ob wohl er anderen namen extra angelegt hat
            #  maybe vorher schauen ob schon _seg da sind und diese so sichern das diese nicht überschrieben werden?
            default_suffix_path = os.path.splitext(image_path)[0] + '_seg.npy'
            if os.path.exists(default_suffix_path):
                os.rename(default_suffix_path, new_path)

            if image_id not in self.csp.mask_paths:
                self.csp.mask_paths[image_id] = {}

            self.csp.mask_paths[image_id][segmentation_channel] = new_path

            progress = str(round((iN + 1) / n_images * 100)) + "%"
            current_image = {"image_id": iN, "path": image_path}
            self._call_update_listeners(progress, current_image)

        end_time_sequential = time()
        print(f"The segmentation lasted {end_time_sequential-start_time_sequential}\n")
        self._call_completion_listeners(self.csp.mask_paths)

    def run_parallel(self):
        """
        runs the segmentation process and saves the mask as npy file
        """
        if self.cancel_now:
            pass
        elif self.pause_now:
            pass
        elif self.resume_now:
            pass
        self._call_start_listeners()
        image_paths = self.csp.image_paths
        segmentation_channel = self.csp.config.get_bf_channel()
        print(segmentation_channel)
        print(image_paths)
        diameter = self.csp.config.get_diameter()
        suffix = self.csp.config.get_mask_suffix()

        segmentation_model = self.csp.model_path
        device = self.device
        device = torch.device(device)  # converts string to device object


        io.logger_setup()  # configures logging system for Cellpose
        model = models.CellposeModel(device=device, pretrained_model=segmentation_model)

        start_time_parallel= time()

        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = []
            for iN, image_id in enumerate(image_paths):
                futures.append(executor.submit(self.image_segmentation,iN,image_id,image_paths,segmentation_channel,diameter,suffix,model))


        end_time_parallel= time()
        print(f"The segmentation took {end_time_parallel-start_time_parallel}\n")
        self._call_completion_listeners(self.csp.mask_paths)

    def image_segmentation(self,iN,image_id,image_paths,segmentation_channel,diameter,suffix,model):
        """
        segments the given image
        Args:
             iN (int): the index of the image
             image_id (str): the id of the image
             image_paths (list): the paths of the images
             segmentation_channel (int): the channel of the segmentation
             diameter (int): the diameter of the segmentation
             suffix (str): the suffix of the segmentation
             model (CellPoseModel) : instance of a CellPoseModel
        """

        n_images = len(image_paths)
        if self.cancel_now:
            self._call_cancel_listeners()
            return
        elif self.pause_now:
            self._call_pause_listeners()
            return
        elif self.resume_now:
            self._call_resume_listeners()
            return

        image_path = image_paths[image_id][segmentation_channel]
        image = imread(image_path)

        res = model.eval(image, diameter=diameter, channels=[0, 0])
        mask, flow, style = res[:3]

        # Generate the output filename directly using the suffix attribute
        directory, filename = os.path.split(image_path)
        name, _ = os.path.splitext(filename)
        new_filename = f"{name}{suffix}.npy"
        new_path = os.path.join(directory, new_filename)

        # Save the segmentation results directly with the default name first
        io.masks_flows_to_seg([image], [mask], [flow], [image_path])

        # Rename the file to the desired name
        # TODO REVIEW by Flo: umbennen hat halt nachteil fällt mir gerade ein,
        #  dass wenn wir segs schon haben diese überschrieben werden ob wohl er anderen namen extra angelegt hat
        #  maybe vorher schauen ob schon _seg da sind und diese so sichern das diese nicht überschrieben werden?
        default_suffix_path = os.path.splitext(image_path)[0] + '_seg.npy'
        if os.path.exists(default_suffix_path):
            os.rename(default_suffix_path, new_path)

        if image_id not in self.csp.mask_paths:
            self.csp.mask_paths[image_id] = {}

        self.csp.mask_paths[image_id][segmentation_channel] = new_path

        progress = str(round((iN + 1) / n_images * 100)) + "%"
        current_image = {"image_id": iN, "path": image_path}
        self._call_update_listeners(progress, current_image)
        self._call_update_listeners(progress, current_image)


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
            print(mask_paths)
            mask_path = mask_paths[image_id][segmentation_channel]
            print("mask path in images", mask_path)
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
