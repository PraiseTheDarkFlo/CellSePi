import os

import numpy as np
from cellpose.io import imread


def calculate_mask_diameters(mask):
    unique_masks = np.unique(mask)
    diameters = []

    for cell_id in unique_masks:
        if cell_id == 0:
            continue
        cell_pixels = np.argwhere(mask == cell_id)
        y_min, x_min = cell_pixels.min(axis=0)
        y_max, x_max = cell_pixels.max(axis=0)
        diameter = np.sqrt((y_max - y_min) ** 2 + (x_max - x_min) ** 2)
        if diameter is not None:
            diameters.append(diameter)
        print(diameter)
    return diameters
    #cell_ids = np.unique(mask)
    #diameters = []
    #cell_ids = cell_ids[1:]

    #for cell_id in cell_ids:
     #   cell_mask = mask == cell_id
      #  cell_area = np.sum(cell_mask)

        # Approximate diameter assuming circular cells
       # cell_diameter = 2 * np.sqrt(cell_area / np.pi)
        #diameters.append(cell_diameter)

    #return diameters

class AverageDiameter:

    def __init__(self, csp):
        self.csp = csp

    def get_avg_diameter(self):
        mask_paths = self.csp.mask_paths
        image_paths = self.csp.image_paths
        segmentation_channel = self.csp.config.get_bf_channel()
        all_diameters = []

        for iN, image_id in enumerate(image_paths):
            mask_path = mask_paths[image_id][segmentation_channel]
            mask_data = np.load(mask_path, allow_pickle=True).item()
            mask = mask_data["masks"]
            diameters = calculate_mask_diameters(mask)
            all_diameters.extend(diameters)
        average_diameter = np.mean(all_diameters)
        return round(average_diameter, 2)





