#the mask is uploaded in the canvas
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
    def __init__(self):
        self.csp= CellSePi()
        self.cells=[]
        self.rectangles=[] #[image_id, data points]
        self.mask_outputs= [] #[image_id,path zu .png]

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
                self.convert_npy_to_canvas(mask,outline)

                #convert the Path back to normal
                pathlib.PosixPath=current_path
        else:
            print(f"mask of {self.csp.image_id} was fetched before")
            return self.mask_outputs["image_id"==self.csp.image_id]



    def convert_npy_to_canvas(self,mask, outline):
        # Variant #1

        mask_ids = np.unique(mask)[1:]

        image_mask = np.zeros(shape=(mask.shape[0], mask.shape[1], 4), dtype=np.uint8)
        image_mask[mask != 0] = (255, 0, 0, 128)
        image_mask[outline != 0] = (0, 255, 0, 255)
        im= Image.fromarray(image_mask).convert("RGBA")
        im.resize(size=(700,500))
        im.save(f"mask_{self.csp.image_id}_seg.png")
        #path="..\mask_{self.csp.image_id}_seg.png"
       # self.mask_outputs.append({"image_id":mask_ids,"path":path})

        """
        #Attempt #1 to save the cells as data points for the adaptation of cells
        for y in range(mask.shape[0]):
            for x in range(mask.shape[1]):
                rgba = [0, 0, 0, 0]  # Standard schwarz/transparenz
                if mask[y, x] != 0:
                    rgba = [255, 0, 0, 128]  # Rote Zellen (halbtransparent)
                if outline[y, x] != 0:
                    rgba = [0, 255, 0, 255]  # Grüne Outline (undurchsichtig)

                # Speichere jede Zelle
                self.cells.append({"x": x, "y": y, "color": rgba})

      
        print("Ich bin in der Methode gewesen")
        rectangles=[]
        cell_size = 50
        for cell in self.cells:
            x, y, color = cell["x"], cell["y"], cell["color"]
            if cell != 0:

                rectangle= fc.Rect(
                    x*cell_size,
                    y*cell_size,
                    cell_size,
                    cell_size,
                    paint=ft.Paint(color=color)
                )
                print("Rec created ")
                rectangles.append(rectangle)
                self.rectangles.append({"image_id":mask_ids,"data":rectangles})

            if outline[y,x] != 0:
                rect=  fc.Rect(
                            x * cell_size,
                            y * cell_size,
                            cell_size,
                            cell_size,
                            paint=ft.Paint(color=color),
                        )
                print("outline created ")
                rectangles.append(rect)
                self.rectangles.append({"image_id": mask_ids, "data": rectangles})


                print(len(self.rectangles))
                """




