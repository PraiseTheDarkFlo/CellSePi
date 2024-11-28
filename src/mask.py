#the mask is uploaded in the canvas
from src.CellSePi import CellSePi
import flet as ft
import flet.canvas as fc
import numpy as np
import pathlib
import platform

#im Moment werden die immer überschrieben. Es wäre eigentlich besser wenn er sich die abspeichert, die er schon mal geladen hat
#dann muss er nur noch darauf zugreifen
class Mask:
    def __init__(self):
        self.csp= CellSePi()
        self.cells=[]
        self.rectangles=[]

    def load_mask_into_canvas(self):

        print ("Display Mask")
        #iterate over the processed data to load the mask images for the current image
        #if self.csp.image_id in self.csp.mask_paths:
        #self.csp.mask_paths[self.csp.image_id][self.csp.config.get_bf_channel()]

        # hier den Path setzen, wenn das Betriebssystem Windows ist.
        current_path = pathlib.PosixPath
        if platform.system() == "Windows":
            pathlib.PosixPath=pathlib.WindowsPath

        mask_data = np.load("xy01c1_seg.npy", allow_pickle=True).item()
        #print(type(mask_data))
        mask= mask_data["masks"]
        outline = mask_data["outlines"]
        #mask_converted =self.convert_npy_to_canvas(mask,outline)
        self.convert_npy_to_canvas(mask,outline)

        #convert the Path back to normal
        pathlib.PosixPath=current_path



    def convert_npy_to_canvas(self,mask, outline):
        mask_ids = np.unique(mask)[1:]
       # image_mask = np.zeros(shape=(mask.shape[0], mask.shape[1], 4), dtype=np.uint8)
       # image_mask[mask != 0] = (255, 0, 0, 128)
       # image_mask[outline != 0] = (0, 255, 0, 255)

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
                self.rectangles.append(rectangle)
            if outline[y,x] != 0:
                rect=  fc.Rect(
                            x * cell_size,
                            y * cell_size,
                            cell_size,
                            cell_size,
                            paint=ft.Paint(color=color),
                        )
                print("outline created ")
                self.rectangles.append(rect)

        print(len(self.rectangles))

        #im= Image.fromarray(image_mask).convert("RGBA")
        #im.resize(size=(700,500))
        #im.save(f"image_xy01c1_seg.png")



