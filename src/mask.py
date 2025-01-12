#the mask is uploaded in the canvas
import os.path

from src.CellSePi import CellSePi
import flet as ft
import flet.canvas as fc
import numpy as np
import pathlib
import platform
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
    def __init__(self,CellSePi):
        self.csp= CellSePi
        # the path to the already generated masks are stored in here
        self.mask_outputs = defaultdict(dict)# [image_id,path zu .png]

    def load_mask_into_canvas(self):
        """
        loads the numpy files of the mask to the id and converts it to png
        """
        print ("Display Mask")
        #iterate over the processed data to load the mask images for the current image
        if self.csp.image_id in self.csp.mask_paths:

            # if operating system is Windows set the pathLib to Windows path
            current_path = pathlib.PosixPath
            if platform.system() == "Windows":
                pathlib.PosixPath=pathlib.WindowsPath

            #load the npy file and convert it to directory
            mask_data = np.load(self.csp.mask_paths[self.csp.image_id][self.csp.config.get_bf_channel()], allow_pickle=True).item()

            #extract the mask data and the outline of the cell
            mask= mask_data["masks"]
            outline = mask_data["outlines"]
            self.convert_npy_to_canvas(mask,outline)

            #convert the Path back to normal
            pathlib.PosixPath=current_path


        else:
            print(f"{self.csp.image_id} is not in mask paths")


    def convert_npy_to_canvas(self,mask, outline):
        """
        handles the convertation of the given file data

        Args:
            mask= the mask data stored in the numpy directory
            outline= the outline data stored in the numpy directory
        """

        image_mask = np.zeros(shape=(mask.shape[0], mask.shape[1], 4), dtype=np.uint8)
        r,g,b = self.csp.config.get_mask_color()
        image_mask[mask != 0] = (r, g, b, 128)
        r, g, b = self.csp.config.get_outline_color()
        image_mask[outline != 0] = (r, g, b, 255)
        im= Image.fromarray(image_mask).convert("RGBA")
        im.resize(size=(700,500))

        #create the output path independent of operating system
        brightfield_channel=self.csp.config.get_bf_channel()
        suffix=self.csp.config.get_channel_prefix()
        directory = os.path.dirname(self.csp.mask_paths[self.csp.image_id][brightfield_channel])
        file_path= os.sep.join([directory, f"mask_{self.csp.image_id}{suffix}{brightfield_channel}_seg.png"])
        im.save(file_path,"png")
        print (f"image is saved in {file_path}")

        #saves the created output image.
        self.mask_outputs[self.csp.image_id][brightfield_channel]=file_path






