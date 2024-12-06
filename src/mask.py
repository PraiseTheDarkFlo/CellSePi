#the mask is uploaded in the canvas
import os.path

from src.CellSePi import CellSePi
import flet as ft
import flet.canvas as fc
import numpy as np
import pathlib
import platform
from PIL import Image

#im Moment werden die immer überschrieben. Es wäre eigentlich besser wenn er sich die abspeichert, die er schon mal geladen hat
#dann muss er nur noch darauf zugreifen
class Mask:
    def __init__(self,CellSePi):
        self.csp= CellSePi
        self.output_saved=False
        self.mask_outputs= {} #[image_id,path zu .png]

    def load_mask_into_canvas(self):

        print ("Display Mask")
        #iterate over the processed data to load the mask images for the current image
        if self.csp.image_id in self.csp.mask_paths:

            # if operating system is Windows set the pathLib to Windows path
            if self.csp.image_id not in self.mask_outputs:
                current_path = pathlib.PosixPath
                if platform.system() == "Windows":
                    pathlib.PosixPath=pathlib.WindowsPath

                #load the npy file and convert it to directory
                mask_data = np.load(self.csp.mask_paths[self.csp.image_id][self.csp.config.get_bf_channel()], allow_pickle=True).item()

                #extract the mask data and the outline of the cell
                mask= mask_data["masks"]
                outline = mask_data["outlines"]
                #mask_converted =self.convert_npy_to_canvas(mask,outline)
                path= self.convert_npy_to_canvas(mask,outline)

                #convert the Path back to normal
                pathlib.PosixPath=current_path
                #self.output_saved=True
                return path
            else:
                print(f"mask of {self.csp.image_id} was fetched before")
                #return self.mask_outputs["image_id"==self.csp.image_id]

        else:
            print(f"{self.csp.image_id} is not in mask paths")
            #self.output_saved=False


    def convert_npy_to_canvas(self,mask, outline):
        # Variant #1
        image_mask = np.zeros(shape=(mask.shape[0], mask.shape[1], 4), dtype=np.uint8)
        image_mask[mask != 0] = (255, 0, 0, 128)
        image_mask[outline != 0] = (0, 255, 0, 255)
        im= Image.fromarray(image_mask).convert("RGBA")
        im.resize(size=(700,500))

        #create the output path independent of operating system
        brightfield_channel=self.csp.config.get_bf_channel()
        suffix=self.csp.config.get_channel_prefix()
        directory = os.path.dirname(self.csp.mask_paths[self.csp.image_id][brightfield_channel])
        file_path= os.sep.join([directory, f"mask_{self.csp.image_id}{suffix}{brightfield_channel}_seg.png"])
        im.save(file_path,"png")
        print (f"image is saved in {file_path}")

        #saves the already stored data.
       # path=f"..\mask_{self.csp.image_id}_seg.png"
        self.mask_outputs[self.csp.image_id]=file_path
        return file_path





