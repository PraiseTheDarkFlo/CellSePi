import base64
from io import BytesIO
from pathlib import Path

from cellsepi.backend.main_window.cellsepi import CellSePi
import numpy as np
from PIL import Image
from collections import defaultdict


class Mask:
    """
    in the class the created numpy files of the mask are converted
    in a displayable format (png)

    Attributes:
        csp=current CellSePi object
        mask_outputs= stores the already converted mask outputs, consists
                      of image_id and the path
    """
    def __init__(self,csp:CellSePi):
        self.csp= csp
        # the path to the already generated masks are stored in here
        self.mask_outputs = defaultdict(dict)# [image_id,path zu .png]

    def load_mask_into_canvas(self):
        """
        loads the numpy files of the mask to the id and converts it to png
        """
        #iterate over the processed data to load the mask images for the current image
        image_id = self.csp.image_id
        bfc= self.csp.config.get_bf_channel()
        if image_id in self.csp.mask_paths:

            #load the npy file and convert it to directory
            mask_data = np.load(Path(self.csp.mask_paths[image_id][bfc]), allow_pickle=True).item()

            #extract the mask data and the outline of the cell
            mask= mask_data["masks"]
            outline = mask_data["outlines"]
            self.convert_npy_to_canvas(mask,outline)



    def convert_npy_to_canvas(self,mask, outline):
        """
        handles the conversion of the given file data

        Args:
            mask= the mask data stored in the numpy directory
            outline= the outline data stored in the numpy directory
        """
        buffer= BytesIO()


        image_mask = np.zeros(shape=(mask.shape[0], mask.shape[1], 4), dtype=np.uint8)
        r,g,b = self.csp.config.get_mask_color()
        image_mask[mask != 0] = (r, g, b, self.csp.color_opacity)
        r, g, b = self.csp.config.get_outline_color()
        image_mask[outline != 0] = (r, g, b, 255)
        im= Image.fromarray(image_mask).convert("RGBA")
        im.resize(size=(700,500))

        #saves the image as a image(base64)
        im.save(buffer, format="PNG")
        buffer.seek(0)
        image_base_64= base64.b64encode(buffer.getvalue()).decode('utf-8')

        #create the output path independent of operating system
        brightfield_channel=self.csp.config.get_bf_channel()
        image_id=self.csp.image_id

        #saves the created output image.
        self.mask_outputs[image_id][brightfield_channel]=image_base_64







